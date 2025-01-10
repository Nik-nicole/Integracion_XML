import xml.etree.ElementTree as ET
from flask import Blueprint, request, jsonify, render_template
from io import BytesIO
from app import db
from app.models.models import Empresa, InformacionTerceros, Facturacion
import json
from markupsafe import Markup

# Crear el Blueprint
xml_upload_bp = Blueprint('xml_upload', __name__)

# Ruta para mostrar el formulario y procesar el archivo XML
@xml_upload_bp.route('/upload', methods=['GET', 'POST'])
def upload_xml():
    if request.method == 'POST':
        # Verificar si el archivo está en la solicitud
        if 'xml_file' not in request.files:
            return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
        file = request.files['xml_file']

        # Verificar si el archivo tiene un nombre válido
        if file.filename == '':
            return jsonify({'error': 'No se seleccionó un archivo'}), 400

        if file:
            # Leer el archivo en memoria usando BytesIO
            file_content = BytesIO(file.read())

            # Procesar el archivo XML directamente desde la memoria
            try:
                datos, facturacion, productos = parse_xml(file_content)
                
                # Imprimir los datos por consola
                print_data(datos)
                print("Facturación Extraída:")
                for factura in facturacion:
                    print(factura)
                print("Productos Extraídos:")
                for producto in productos:
                    print(producto)
                
                # Renderizar la plantilla con los datos extraídos
                return render_template('upload_xml.html', datos=datos, facturacion=facturacion, productos=productos)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    return render_template('upload_xml.html')

@xml_upload_bp.route('/export_data', methods=['POST'])
def export_data():
    try:
        # Obtener los datos del formulario
        datos = request.form.get('datos')
        facturacion = request.form.get('facturacion')
        productos = request.form.get('productos')
        
        # Debug: imprimir los datos recibidos
        print("Datos recibidos:", datos)
        print("Facturación recibida:", facturacion)
        print("Productos recibidos:", productos)
        
        # Verificar si los datos están presentes
        if not datos or not facturacion or not productos:
            return jsonify({
                'status': 'error',
                'message': 'Datos incompletos',
                'received': {
                    'datos': bool(datos),
                    'facturacion': bool(facturacion),
                    'productos': bool(productos)
                }
            }), 400

        # Convertir los datos JSON a diccionarios de Python
        try:
            datos = json.loads(datos)
            facturacion = json.loads(facturacion)
            productos = json.loads(productos)
        except json.JSONDecodeError as e:
            return jsonify({
                'status': 'error',
                'message': f'Error al decodificar JSON: {str(e)}',
                'datos_recibidos': {
                    'datos': datos[:100] if datos else None,  # Mostrar primeros 100 caracteres
                    'facturacion': facturacion[:100] if facturacion else None,
                    'productos': productos[:100] if productos else None
                }
            }), 400

        # Guardar en la base de datos
        save_to_db(datos, facturacion)

        return jsonify({
            'status': 'success',
            'message': 'Datos guardados correctamente',
            'datos': datos,
            'facturacion': facturacion,
            'productos': productos
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error general: {str(e)}'
        }), 500

def parse_xml(file_content):
    tree = ET.parse(file_content)
    root = tree.getroot()

    namespaces = {
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
        'sts': 'dian:gov:co:facturaelectronica:Structures-2-1'
    }

    datos = []
    facturacion = []
    productos = []

    # Buscar el nodo <cbc:Description> que contiene el CDATA con el XML interno
    description_node = root.find('.//cbc:Description', namespaces=namespaces)
    if description_node is not None and description_node.text:
        # Extraer el contenido CDATA
        inner_xml_content = description_node.text.strip()
        print("CDATA Content Extracted:\n", inner_xml_content)  # Imprimir el contenido CDATA extraído

        # Parsear el contenido CDATA como un nuevo XML
        try:
            inner_tree = ET.ElementTree(ET.fromstring(inner_xml_content))
            inner_root = inner_tree.getroot()

            # Extraer la información del emisor y receptor del XML interno
            supplier_party = inner_root.find('cac:AccountingSupplierParty/cac:Party', namespaces=namespaces)
            supplier_info = extract_party_info(supplier_party, namespaces)
            datos.append(supplier_info)

            customer_party = inner_root.find('cac:AccountingCustomerParty/cac:Party', namespaces=namespaces)
            customer_info = extract_party_info(customer_party, namespaces)
            datos.append(customer_info)

            # Extraer la información de facturación
            tax_total = inner_root.find('cac:TaxTotal', namespaces=namespaces)
            if tax_total is not None:
                tax_amount = tax_total.findtext('cbc:TaxAmount', namespaces=namespaces)
                facturacion.append({'campo': 'Monto de Impuestos', 'valor': tax_amount})

            legal_monetary_total = inner_root.find('cac:LegalMonetaryTotal', namespaces=namespaces)
            if legal_monetary_total is not None:
                line_extension_amount = legal_monetary_total.findtext('cbc:LineExtensionAmount', namespaces=namespaces)
                tax_exclusive_amount = legal_monetary_total.findtext('cbc:TaxExclusiveAmount', namespaces=namespaces)
                tax_inclusive_amount = legal_monetary_total.findtext('cbc:TaxInclusiveAmount', namespaces=namespaces)
                prepaid_amount = legal_monetary_total.findtext('cbc:PrepaidAmount', namespaces=namespaces)
                payable_amount = legal_monetary_total.findtext('cbc:PayableAmount', namespaces=namespaces)

                facturacion.append({'campo': 'Monto Total de Líneas', 'valor': line_extension_amount})
                facturacion.append({'campo': 'Monto Total Sin Impuestos', 'valor': tax_exclusive_amount})
                facturacion.append({'campo': 'Monto Total Con Impuestos', 'valor': tax_inclusive_amount})
                facturacion.append({'campo': 'Monto Pre-Pagado', 'valor': prepaid_amount})
                facturacion.append({'campo': 'Monto a Pagar', 'valor': payable_amount})

            # Extraer la información del nodo <cbc:Note>
            note_node = inner_root.find('.//cbc:Note', namespaces=namespaces)
            if note_node is not None and note_node.text:
                # Extraer el contenido de <cbc:Note> y colocarlo como 'valor'
                facturacion.append({'campo': 'Curso de Excel Intermedio', 'valor': note_node.text.strip()})
                print("Note Content found:", note_node.text.strip())
                
            price_amount = inner_root.find('.//cbc:PriceAmount', namespaces=namespaces)
            if price_amount is not None:
                facturacion.append({'campo': 'Costo individual', 'valor': price_amount.text.strip()})
                print("Price Amount found:", price_amount.text.strip())
                
            descripcion_producto = inner_root.find('.//cbc:Description', namespaces=namespaces)
            if descripcion_producto is not None:
                facturacion.append({'campo': 'Descripcion Producto', 'valor': descripcion_producto.text.strip()})
                print("Producto Encontrado:", descripcion_producto.text.strip())
                
            # Extraer el código del producto
            codigo_producto = inner_root.find('.//cac:StandardItemIdentification/cbc:ID', namespaces=namespaces)
            if codigo_producto is not None:
                facturacion.append({'campo': 'Código Producto', 'valor': codigo_producto.text.strip()})
                print("Código Producto Encontrado:", codigo_producto.text.strip())

            # Extraer el valor de la retención en la fuente
            withholding_tax_total = inner_root.find('.//cac:WithholdingTaxTotal/cbc:TaxAmount', namespaces=namespaces)
            if withholding_tax_total is not None:
                facturacion.append({'campo': 'Retención en la Fuente', 'valor': withholding_tax_total.text.strip()})
                print("Retención en la Fuente Encontrada:", withholding_tax_total.text.strip())

            # Extraer la información de los productos
            invoice_lines = inner_root.findall('.//cac:InvoiceLine', namespaces=namespaces)
            for line in invoice_lines:
                nro = line.findtext('cbc:ID', namespaces=namespaces)
                codigo = line.findtext('.//cac:StandardItemIdentification/cbc:ID', namespaces=namespaces)
                descripcion = line.findtext('.//cbc:Description', namespaces=namespaces)
                um = line.findtext('.//cbc:BaseQuantity', namespaces=namespaces)
                cantidad = line.findtext('.//cbc:InvoicedQuantity', namespaces=namespaces)
                precio_unitario = line.findtext('.//cbc:PriceAmount', namespaces=namespaces)
                precio_venta = line.findtext('.//cbc:LineExtensionAmount', namespaces=namespaces)
                descuento_detalle = '0.00'  # Asumimos que no hay descuento detalle
                recargo_detalle = '0.00'  # Asumimos que no hay recargo detalle
                iva = line.findtext('.//cac:TaxTotal/cbc:TaxAmount', namespaces=namespaces)
                inc = '0.00'  # Asumimos que no hay INC

                productos.append({
                    'nro': nro,
                    'codigo': codigo,
                    'descripcion': descripcion,
                    'um': um,
                    'cantidad': cantidad,
                    'precio_unitario': precio_unitario,
                    'precio_venta': precio_venta,
                    'descuento_detalle': descuento_detalle,
                    'recargo_detalle': recargo_detalle,
                    'iva': iva,
                    'inc': inc
                })

        except ET.ParseError as e:
            print("Error parsing inner XML:", e)
        except Exception as e:
            print("Unexpected error:", e)
    else:
        print("Description node not found or empty")

    return datos, facturacion, productos

def extract_party_info(party, namespaces):
    if party is None:
        return {
            'registration_name': 'N/A',
            'company_id': 'N/A',
            'tax_level_code': 'N/A',
            'address': 'N/A',
            'city_name': 'N/A',
            'country_subentity': 'N/A',
            'country_subentity_code': 'N/A',
            'country': 'N/A',
            'country_name': 'N/A',
            'telephone': 'N/A',
            'electronic_mail': 'N/A'
        }

    info = {
        'registration_name': party.findtext('.//cac:PartyTaxScheme/cbc:RegistrationName', namespaces=namespaces),
        'company_id': party.findtext('.//cac:PartyTaxScheme/cbc:CompanyID', namespaces=namespaces),
        'tax_level_code': party.findtext('.//cac:PartyTaxScheme/cbc:TaxLevelCode', namespaces=namespaces),
        'address': party.findtext('.//cac:PhysicalLocation/cac:Address/cac:AddressLine/cbc:Line', namespaces=namespaces),
        'city_name': party.findtext('.//cac:PhysicalLocation/cac:Address/cbc:CityName', namespaces=namespaces),
        'country_subentity': party.findtext('.//cac:PhysicalLocation/cac:Address/cbc:CountrySubentity', namespaces=namespaces),
        'country_subentity_code': party.findtext('.//cac:PhysicalLocation/cac:Address/cbc:CountrySubentityCode', namespaces=namespaces),
        'country': party.findtext('.//cac:PhysicalLocation/cac:Address/cac:Country/cbc:IdentificationCode', namespaces=namespaces),
        'country_name': party.findtext('.//cac:PhysicalLocation/cac:Address/cac:Country/cbc:Name', namespaces=namespaces),
        'telephone': party.findtext('.//cac:Contact/cbc:Telephone', namespaces=namespaces),
        'electronic_mail': party.findtext('.//cac:Contact/cbc:ElectronicMail', namespaces=namespaces)
    }

    print("Extracted info:", info)  # Imprimir la información extraída por consola

    return info

def print_data(datos):
    print("Datos Extraídos:")
    for dato in datos:
        print("Identificación:", dato.get('company_id', 'N/A'))
        print("Nombre/Razón Social:", dato.get('registration_name', 'N/A'))
        print("Tipo Persona:", dato.get('tax_level_code', 'N/A'))
        print("Dirección:", dato.get('address', 'N/A'))
        print("Ciudad:", dato.get('city_name', 'N/A'))
        print("Subentidad del País:", dato.get('country_subentity', 'N/A'))
        print("Código de Subentidad del País:", dato.get('country_subentity_code', 'N/A'))
        print("País:", dato.get('country', 'N/A'))
        print("Nombre del País:", dato.get('country_name', 'N/A'))
        print("Teléfono:", dato.get('telephone', 'N/A'))
        print("Email:", dato.get('electronic_mail', 'N/A'))
        print("-------------------------------")

def save_to_db(datos, facturacion):
    try:
        for dato in datos:
            empresa = InformacionTerceros(
                registration_name=dato['registration_name'],
                company_id=dato['company_id'],
                tax_level_code=dato['tax_level_code'],
                address=dato['address'],
                city_name=dato['city_name'],
                country_subentity=dato['country_subentity'],
                country_subentity_code=dato['country_subentity_code'],
                country=dato['country'],
                country_name=dato['country_name'],
                telephone=dato['telephone'],
                electronic_mail=dato['electronic_mail']
            )
            db.session.add(empresa)

        for factura in facturacion:
            fact = Facturacion(
                campo=factura['campo'],
                valor=factura['valor']
            )
            db.session.add(fact)

        db.session.commit()

    except Exception as e:
        print(f"Error al guardar en la base de datos: {e}")
        db.session.rollback()
    finally:
        db.session.close()
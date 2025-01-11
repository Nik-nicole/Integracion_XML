import xml.etree.ElementTree as ET
from flask import Blueprint, request, jsonify, render_template
from io import BytesIO
from app import db
from app.models.models import Empresa, InformacionTerceros, Facturacion, InvoiceLine
import json

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
                datos, facturacion, productos, impuestos, notas = parse_xml(file_content)
                
                # Imprimir los datos por consola
                print_data(datos)
                print("Facturación Extraída:")
                for factura in facturacion:
                    print(factura)
                print("Productos Extraídos:")
                for producto in productos:
                    print(producto)
                print("Impuestos Extraídos:")
                for impuesto in impuestos:
                    print(impuesto)
                print("Notas Extraídas:")
                for nota in notas:
                    print(nota)
                
                # Renderizar la plantilla con los datos extraídos
                return render_template('upload_xml.html', datos=datos, facturacion=facturacion, productos=productos, impuestos=impuestos, notas=notas)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    return render_template('upload_xml.html')

@xml_upload_bp.route('/export_data', methods=['POST'])
def export_data():
    # Obtener los datos del formulario
    datos = request.form.get('datos')
    facturacion = request.form.get('facturacion')
    productos = request.form.get('productos')
    impuestos = request.form.get('impuestos')
    notas = request.form.get('notas')
    
    # Verificar si los datos están presentes
    if not datos or not facturacion or not productos or not impuestos or not notas:
        return jsonify({'status': 'error', 'message': 'Datos, facturación, productos, impuestos o notas no proporcionados'}), 400

    # Convertir los datos JSON a diccionarios de Python
    try:
        datos = json.loads(datos)
        facturacion = json.loads(facturacion)
        productos = json.loads(productos)
        impuestos = json.loads(impuestos)
        notas = json.loads(notas)
    except json.JSONDecodeError as e:
        return jsonify({'status': 'error', 'message': f'Error al decodificar JSON: {str(e)}'}), 400
    
    # Guardar los datos en la base de datos
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
                ubl_version_id=factura['ubl_version_id'],
                customization_id=factura['customization_id'],
                profile_id=factura['profile_id'],
                profile_execution_id=factura['profile_execution_id'],
                document_id=factura['document_id'],
                uuid=factura['uuid'],
                issue_date=factura['issue_date'],
                issue_time=factura['issue_time'],
                due_date=factura['due_date'],
                invoice_type_code=factura['invoice_type_code'],
                document_currency_code=factura['document_currency_code'],
                line_count_numeric=factura['line_count_numeric'],
                supplier_id=factura['supplier_id'],
                customer_id=factura['customer_id']
            )
            db.session.add(fact)

        for producto in productos:
            line = InvoiceLine(
                line_id=producto['nro'],
                codigo=producto['codigo'],
                descripcion=producto['descripcion'],
                um=producto['um'],
                cantidad=producto['cantidad'],
                precio_unitario=producto['precio_unitario'],
                precio_venta=producto['precio_venta'],
                descuento_detalle=producto['descuento_detalle'],
                recargo_detalle=producto['recargo_detalle'],
                iva=producto['iva'],
                inc=producto['inc']
            )
            db.session.add(line)

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Datos exportados correctamente'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Error al guardar en la base de datos: {str(e)}'}), 500

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
    impuestos = []
    notas = []

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
            facturacion_data = {
                'ubl_version_id': inner_root.findtext('cbc:UBLVersionID', namespaces=namespaces),
                'customization_id': inner_root.findtext('cbc:CustomizationID', namespaces=namespaces),
                'profile_id': inner_root.findtext('cbc:ProfileID', namespaces=namespaces),
                'profile_execution_id': inner_root.findtext('cbc:ProfileExecutionID', namespaces=namespaces),
                'document_id': inner_root.findtext('cbc:ID', namespaces=namespaces),
                'uuid': inner_root.findtext('cbc:UUID', namespaces=namespaces),
                'issue_date': inner_root.findtext('cbc:IssueDate', namespaces=namespaces),
                'issue_time': inner_root.findtext('cbc:IssueTime', namespaces=namespaces),
                'due_date': inner_root.findtext('cbc:DueDate', namespaces=namespaces),
                'invoice_type_code': inner_root.findtext('cbc:InvoiceTypeCode', namespaces=namespaces),
                'document_currency_code': inner_root.findtext('cbc:DocumentCurrencyCode', namespaces=namespaces),
                'line_count_numeric': inner_root.findtext('cbc:LineCountNumeric', namespaces=namespaces),
                'supplier_id': supplier_info['company_id'],
                'customer_id': customer_info['company_id']
            }
            facturacion.append(facturacion_data)

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

            # Extraer la información de impuestos
            tax_totals = inner_root.findall('.//cac:TaxTotal', namespaces=namespaces)
            for tax_total in tax_totals:
                tax_amount = tax_total.findtext('cbc:TaxAmount', namespaces=namespaces)
                tax_subtotals = tax_total.findall('.//cac:TaxSubtotal', namespaces=namespaces)
                for tax_subtotal in tax_subtotals:
                    taxable_amount = tax_subtotal.findtext('cbc:TaxableAmount', namespaces=namespaces)
                    tax_amount_subtotal = tax_subtotal.findtext('cbc:TaxAmount', namespaces=namespaces)
                    tax_percent = tax_subtotal.findtext('.//cbc:Percent', namespaces=namespaces)
                    tax_scheme_id = tax_subtotal.findtext('.//cac:TaxScheme/cbc:ID', namespaces=namespaces)
                    tax_scheme_name = tax_subtotal.findtext('.//cac:TaxScheme/cbc:Name', namespaces=namespaces)

                    impuestos.append({
                        'taxable_amount': taxable_amount,
                        'tax_amount': tax_amount_subtotal,
                        'tax_percent': tax_percent,
                        'tax_scheme_id': tax_scheme_id,
                        'tax_scheme_name': tax_scheme_name
                    })

            # Extraer la información de las notas
            note_nodes = inner_root.findall('.//cbc:Note', namespaces=namespaces)
            for note_node in note_nodes:
                if note_node is not None and note_node.text:
                    notas.append({'nota': note_node.text.strip()})

        except ET.ParseError as e:
            print("Error parsing inner XML:", e)
        except Exception as e:
            print("Unexpected error:", e)
    else:
        print("Description node not found or empty")

    return datos, facturacion, productos, impuestos, notas

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
                ubl_version_id=factura['ubl_version_id'],
                customization_id=factura['customization_id'],
                profile_id=factura['profile_id'],
                profile_execution_id=factura['profile_execution_id'],
                document_id=factura['document_id'],
                uuid=factura['uuid'],
                issue_date=factura['issue_date'],
                issue_time=factura['issue_time'],
                due_date=factura['due_date'],
                invoice_type_code=factura['invoice_type_code'],
                document_currency_code=factura['document_currency_code'],
                line_count_numeric=factura['line_count_numeric'],
                supplier_id=factura['supplier_id'],
                customer_id=factura['customer_id']
            )
            db.session.add(fact)

        db.session.commit()

    except Exception as e:
        print(f"Error al guardar en la base de datos: {e}")
        db.session.rollback()
    finally:
        db.session.close()
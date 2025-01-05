import xml.etree.ElementTree as ET
from flask import Blueprint, request, jsonify, render_template
from io import BytesIO
from app import db
from app.models.models import Empresa, InformacionTerceros, Facturacion
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
                datos, facturacion = parse_xml(file_content)
                
                # Imprimir los datos por consola
                print_data(datos)
                print("Facturación Extraída:")
                for factura in facturacion:
                    print(factura)
                
                # Redirigir a la página donde se mostrarán los datos
                return render_template('upload_xml.html', datos=datos, facturacion=facturacion)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    return render_template('upload_xml.html')

@xml_upload_bp.route('/export_data', methods=['POST'])
def export_data():
    # Obtener los datos del formulario
    datos = request.form.get('datos')
    facturacion = request.form.get('facturacion')
    
    # Convertir los datos JSON a diccionarios de Python
    try:
        datos = json.loads(datos)
        facturacion = json.loads(facturacion)
    except json.JSONDecodeError as e:
        return jsonify({'status': 'error', 'message': f'Error al decodificar JSON: {str(e)}'}), 400
    
    # Guardar los datos en la base de datos
    save_to_db(datos, facturacion)
    
    return jsonify({'status': 'success', 'message': 'Datos exportados correctamente'})

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
            if supplier_party is not None:
                print("Supplier Party found")
            else:
                print("Supplier Party not found")
            supplier_info = extract_party_info(supplier_party, namespaces)
            datos.append(supplier_info)

            customer_party = inner_root.find('cac:AccountingCustomerParty/cac:Party', namespaces=namespaces)
            if customer_party is not None:
                print("Customer Party found")
            else:
                print("Customer Party not found")
            customer_info = extract_party_info(customer_party, namespaces)
            datos.append(customer_info)

            # Extraer la información de facturación
            tax_total = inner_root.find('cac:TaxTotal', namespaces=namespaces)
            if tax_total is not None:
                tax_amount = tax_total.findtext('cbc:TaxAmount', namespaces=namespaces)
                facturacion.append({'campo': 'Monto de Impuestos', 'valor': tax_amount})
                print("Tax Amount found:", tax_amount)  # Depuración

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

                print("Line Extension Amount found:", line_extension_amount)  # Depuración
                print("Tax Exclusive Amount found:", tax_exclusive_amount)  # Depuración
                print("Tax Inclusive Amount found:", tax_inclusive_amount)  # Depuración
                print("Prepaid Amount found:", prepaid_amount)  # Depuración
                print("Payable Amount found:", payable_amount)  # Depuración

        except ET.ParseError as e:
            print("Error parsing inner XML:", e)
    else:
        print("Description node not found or empty")

    return datos, facturacion

def extract_party_info(party, namespaces):
    if party is None:
        return {
            'identificacion': 'N/A',
            'nombre_razon_social': 'N/A',
            'tipo_persona': 'N/A',
            'direccion': 'N/A',
            'telefono': 'N/A',
            'email': 'N/A',
            'actividad_economica': 'N/A'
        }

    info = {
        'identificacion': party.findtext('.//cac:PartyTaxScheme/cbc:CompanyID', namespaces=namespaces),
        'nombre_razon_social': party.findtext('.//cac:PartyTaxScheme/cbc:RegistrationName', namespaces=namespaces),
        'tipo_persona': party.findtext('../cbc:AdditionalAccountID', namespaces=namespaces),
        'direccion': party.findtext('.//cac:PhysicalLocation/cac:Address/cac:AddressLine/cbc:Line', namespaces=namespaces),
        'telefono': party.findtext('.//cac:Contact/cbc:Telephone', namespaces=namespaces),
        'email': party.findtext('.//cac:Contact/cbc:ElectronicMail', namespaces=namespaces),
        'actividad_economica': party.findtext('.//cac:PartyTaxScheme/cbc:IndustryClassificationCode', namespaces=namespaces)
    }

    print("Extracted info:", info)  # Imprimir la información extraída por consola

    return info

def print_data(datos):
    print("Datos Extraídos:")
    for dato in datos:
        print("Identificación:", dato.get('identificacion', 'N/A'))
        print("Nombre/Razón Social:", dato.get('nombre_razon_social', 'N/A'))
        print("Tipo Persona:", dato.get('tipo_persona', 'N/A'))
        print("Dirección:", dato.get('direccion', 'N/A'))
        print("Teléfono:", dato.get('telefono', 'N/A'))
        print("Email:", dato.get('email', 'N/A'))
        print("Actividad Económica:", dato.get('actividad_economica', 'N/A'))
        print("-------------------------------")

def save_to_db(datos, facturacion):
    try:
        for dato in datos:
            empresa = Empresa(
                registration_name=dato['nombre_razon_social'],
                company_id=dato['identificacion'],
                tax_level_code=dato['tipo_persona'],
                address=dato['direccion'],
                telephone=dato['telefono'],
                electronic_mail=dato['email']
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
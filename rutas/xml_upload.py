import xml.etree.ElementTree as ET
from flask import Blueprint, request, jsonify, render_template
from io import BytesIO

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
                datos = parse_xml(file_content)
                # Solo devolver los datos extraídos en formato JSON
                return jsonify(datos)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    return render_template('upload_xml.html')

def parse_xml(file_content):
    # Procesar el archivo XML desde BytesIO
    tree = ET.parse(file_content)
    root = tree.getroot()

    # Definir namespaces
    namespaces = {
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
        'sts': 'dian:gov:co:facturaelectronica:Structures-2-1'
    }

    # Extraer información general del documento
    general_info = {
        'UBLVersionID': root.findtext('cbc:UBLVersionID', namespaces=namespaces),
        'CustomizationID': root.findtext('cbc:CustomizationID', namespaces=namespaces),
        'ProfileID': root.findtext('cbc:ProfileID', namespaces=namespaces),
        'ProfileExecutionID': root.findtext('cbc:ProfileExecutionID', namespaces=namespaces),
        'ID': root.findtext('cbc:ID', namespaces=namespaces),
        'UUID': root.findtext('cbc:UUID', namespaces=namespaces),
        'IssueDate': root.findtext('cbc:IssueDate', namespaces=namespaces),
        'IssueTime': root.findtext('cbc:IssueTime', namespaces=namespaces),
        'DueDate': root.findtext('cbc:DueDate', namespaces=namespaces),
        'InvoiceTypeCode': root.findtext('cbc:InvoiceTypeCode', namespaces=namespaces),
        'DocumentCurrencyCode': root.findtext('cbc:DocumentCurrencyCode', namespaces=namespaces),
        'LineCountNumeric': root.findtext('cbc:LineCountNumeric', namespaces=namespaces)
    }

    # Extraer información del emisor (AccountingSupplierParty)
    supplier_party = root.find('cac:AccountingSupplierParty', namespaces=namespaces)
    supplier_info = extract_supplier_data(supplier_party, namespaces)

    # Extraer información del receptor (AccountingCustomerParty)
    customer_party = root.find('cac:AccountingCustomerParty', namespaces=namespaces)
    customer_info = extract_customer_data(customer_party, namespaces)

    # Extraer información de la línea de factura (InvoiceLine)
    invoice_lines = []
    for line in root.findall('cac:InvoiceLine', namespaces=namespaces):
        invoice_lines.append(extract_invoice_line_data(line, namespaces))

    # Extraer información del documento adjunto (Attachment)
    attachment = root.find('.//cbc:Description', namespaces=namespaces)
    attachment_info = extract_attachment_data(attachment.text) if attachment is not None else {}

    return {
        'general_info': general_info,
        'supplier_info': supplier_info,
        'customer_info': customer_info,
        'invoice_lines': invoice_lines,
        'attachment_info': attachment_info
    }

def extract_supplier_data(supplier_party, namespaces):
    if supplier_party is None:
        return {}

    party = supplier_party.find('cac:Party', namespaces=namespaces)
    address = party.find('cac:PhysicalLocation/cac:Address', namespaces=namespaces)
    contact = party.find('cac:Contact', namespaces=namespaces)
    party_tax_scheme = party.find('cac:PartyTaxScheme', namespaces=namespaces)
    party_legal_entity = party.find('cac:PartyLegalEntity', namespaces=namespaces)
    registration_address = party_tax_scheme.find('cac:RegistrationAddress', namespaces=namespaces)
    tax_scheme = party_tax_scheme.find('cac:TaxScheme', namespaces=namespaces)
    corporate_registration_scheme = party_legal_entity.find('cac:CorporateRegistrationScheme', namespaces=namespaces)

    return {
        'AdditionalAccountID': supplier_party.findtext('cbc:AdditionalAccountID', namespaces=namespaces),
        'IndustryClassificationCode': supplier_party.findtext('cbc:IndustryClassificationCode', namespaces=namespaces),
        'PartyName': party.findtext('cac:PartyName/cbc:Name', namespaces=namespaces),
        'Address': {
            'ID': address.findtext('cbc:ID', namespaces=namespaces) or '',
            'CityName': address.findtext('cbc:CityName', namespaces=namespaces) or '',
            'CountrySubentity': address.findtext('cbc:CountrySubentity', namespaces=namespaces) or '',
            'CountrySubentityCode': address.findtext('cbc:CountrySubentityCode', namespaces=namespaces) or '',
            'Line': address.findtext('cac:AddressLine/cbc:Line', namespaces=namespaces) or '',
            'CountryIdentificationCode': address.findtext('cac:Country/cbc:IdentificationCode', namespaces=namespaces) or '',
            'CountryName': address.findtext('cac:Country/cbc:Name', namespaces=namespaces) or ''
        },
        'PartyTaxScheme': {
            'RegistrationName': party_tax_scheme.findtext('cbc:RegistrationName', namespaces=namespaces) or '',
            'CompanyID': party_tax_scheme.findtext('cbc:CompanyID', namespaces=namespaces) or '',
            'TaxLevelCode': party_tax_scheme.findtext('cbc:TaxLevelCode', namespaces=namespaces) or '',
            'RegistrationAddress': {
                'ID': registration_address.findtext('cbc:ID', namespaces=namespaces) or '',
                'CityName': registration_address.findtext('cbc:CityName', namespaces=namespaces) or '',
                'CountrySubentity': registration_address.findtext('cbc:CountrySubentity', namespaces=namespaces) or '',
                'CountrySubentityCode': registration_address.findtext('cbc:CountrySubentityCode', namespaces=namespaces) or '',
                'Line': registration_address.findtext('cac:AddressLine/cbc:Line', namespaces=namespaces) or '',
                'CountryIdentificationCode': registration_address.findtext('cac:Country/cbc:IdentificationCode', namespaces=namespaces) or '',
                'CountryName': registration_address.findtext('cac:Country/cbc:Name', namespaces=namespaces) or ''
            },
            'TaxScheme': {
                'ID': tax_scheme.findtext('cbc:ID', namespaces=namespaces) or '',
                'Name': tax_scheme.findtext('cbc:Name', namespaces=namespaces) or ''
            }
        },
        'PartyLegalEntity': {
            'RegistrationName': party_legal_entity.findtext('cbc:RegistrationName', namespaces=namespaces) or '',
            'CompanyID': party_legal_entity.findtext('cbc:CompanyID', namespaces=namespaces) or '',
            'CorporateRegistrationScheme': {
                'ID': corporate_registration_scheme.findtext('cbc:ID', namespaces=namespaces) or ''
            }
        },
        'Contact': {
            'Telephone': contact.findtext('cbc:Telephone', namespaces=namespaces) or '',
            'ElectronicMail': contact.findtext('cbc:ElectronicMail', namespaces=namespaces) or ''
        }
    }

def extract_customer_data(customer_party, namespaces):
    if customer_party is None:
        return {}

    party = customer_party.find('cac:Party', namespaces=namespaces)
    address = party.find('cac:PhysicalLocation/cac:Address', namespaces=namespaces)
    contact = party.find('cac:Contact', namespaces=namespaces)
    party_tax_scheme = party.find('cac:PartyTaxScheme', namespaces=namespaces)
    party_legal_entity = party.find('cac:PartyLegalEntity', namespaces=namespaces)
    registration_address = party_tax_scheme.find('cac:RegistrationAddress', namespaces=namespaces)
    tax_scheme = party_tax_scheme.find('cac:TaxScheme', namespaces=namespaces)

    return {
        'AdditionalAccountID': customer_party.findtext('cbc:AdditionalAccountID', namespaces=namespaces),
        'PartyName': party.findtext('cac:PartyName/cbc:Name', namespaces=namespaces),
        'Address': {
            'ID': address.findtext('cbc:ID', namespaces=namespaces) or '',
            'CityName': address.findtext('cbc:CityName', namespaces=namespaces) or '',
            'PostalZone': address.findtext('cbc:PostalZone', namespaces=namespaces) or '',
            'CountrySubentity': address.findtext('cbc:CountrySubentity', namespaces=namespaces) or '',
            'CountrySubentityCode': address.findtext('cbc:CountrySubentityCode', namespaces=namespaces) or '',
            'Line': address.findtext('cac:AddressLine/cbc:Line', namespaces=namespaces) or '',
            'CountryIdentificationCode': address.findtext('cac:Country/cbc:IdentificationCode', namespaces=namespaces) or '',
            'CountryName': address.findtext('cac:Country/cbc:Name', namespaces=namespaces) or ''
        },
        'PartyTaxScheme': {
            'RegistrationName': party_tax_scheme.findtext('cbc:RegistrationName', namespaces=namespaces) or '',
            'CompanyID': party_tax_scheme.findtext('cbc:CompanyID', namespaces=namespaces) or '',
            'TaxLevelCode': party_tax_scheme.findtext('cbc:TaxLevelCode', namespaces=namespaces) or '',
            'RegistrationAddress': {
                'ID': registration_address.findtext('cbc:ID', namespaces=namespaces) or '',
                'CityName': registration_address.findtext('cbc:CityName', namespaces=namespaces) or '',
                'CountrySubentity': registration_address.findtext('cbc:CountrySubentity', namespaces=namespaces) or '',
                'CountrySubentityCode': registration_address.findtext('cbc:CountrySubentityCode', namespaces=namespaces) or '',
                'Line': registration_address.findtext('cac:AddressLine/cbc:Line', namespaces=namespaces) or '',
                'CountryIdentificationCode': registration_address.findtext('cac:Country/cbc:IdentificationCode', namespaces=namespaces) or '',
                'CountryName': registration_address.findtext('cac:Country/cbc:Name', namespaces=namespaces) or ''
            },
            'TaxScheme': {
                'ID': tax_scheme.findtext('cbc:ID', namespaces=namespaces) or '',
                'Name': tax_scheme.findtext('cbc:Name', namespaces=namespaces) or ''
            }
        }
    }

def extract_invoice_line_data(line, namespaces):
    return {
        'ID': line.findtext('cbc:ID', namespaces=namespaces) or '',
        'InvoicedQuantity': line.findtext('cbc:InvoicedQuantity', namespaces=namespaces) or '',
        'LineExtensionAmount': line.findtext('cbc:LineExtensionAmount', namespaces=namespaces) or '',
        'Item': {
            'Name': line.findtext('cac:Item/cbc:Name', namespaces=namespaces) or '',
            'Description': line.findtext('cac:Item/cbc:Description', namespaces=namespaces) or ''
        },
        'Price': {
            'PriceAmount': line.findtext('cac:Price/cbc:PriceAmount', namespaces=namespaces) or '',
            'BaseQuantity': line.findtext('cac:Price/cbc:BaseQuantity', namespaces=namespaces) or ''
        }
    }

def extract_attachment_data(description_text):
    return {
        'Description': description_text or ''
    }

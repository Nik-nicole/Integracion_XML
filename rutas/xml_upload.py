import xml.etree.ElementTree as ET
from flask import Blueprint, request, render_template, flash, redirect, url_for
from extensions import db
from app.models.models import InformacionTerceros, Empresa
from io import BytesIO

# Crear el Blueprint
xml_upload_bp = Blueprint('xml_upload', __name__)

# Ruta para mostrar el formulario y procesar el archivo XML
@xml_upload_bp.route('/upload', methods=['GET', 'POST'])
def upload_xml():
    if request.method == 'POST':
        # Verificar si el archivo está en la solicitud
        if 'xml_file' not in request.files:
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        file = request.files['xml_file']

        # Verificar si el archivo tiene un nombre válido
        if file.filename == '':
            flash('No se seleccionó un archivo', 'danger')
            return redirect(request.url)

        if file:
            # Leer el archivo en memoria usando BytesIO
            file_content = BytesIO(file.read())

            # Procesar el archivo XML directamente desde la memoria
            parse_and_save_xml(file_content)

            flash('Archivo XML cargado y procesado exitosamente', 'success')
            return redirect(url_for('xml_upload.upload_xml'))

    return render_template('upload_xml.html')

def parse_and_save_xml(file_content):
    try:
        # Procesar el archivo XML desde BytesIO
        tree = ET.parse(file_content)
        root = tree.getroot()

        # Si no hay namespaces, omite el uso de `root.nsmap`
        namespaces = {
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
        }

        with db.session.begin():  # Usar session.begin() para el manejo adecuado de transacciones
            # Extraer y guardar la información de InformacionTerceros
            for tercero in root.findall('.//cac:PartyTaxScheme', namespaces=namespaces):
                identificacion = tercero.find('cbc:CompanyID', namespaces=namespaces)
                nombre_razon_social = tercero.find('cbc:RegistrationName', namespaces=namespaces)
                tipo_persona = tercero.find('cbc:TaxLevelCode', namespaces=namespaces)
                direccion = tercero.find('cac:RegistrationAddress/cac:AddressLine/cbc:Line', namespaces=namespaces)
                telefono = tercero.find('cac:Contact/cbc:Telephone', namespaces=namespaces)
                email = tercero.find('cac:Contact/cbc:ElectronicMail', namespaces=namespaces)
                actividad_economica = tercero.find('cbc:IndustryClassificationCode', namespaces=namespaces)

                # Validar si cada valor existe antes de asignar
                identificacion = identificacion.text if identificacion is not None else 'No disponible'
                nombre_razon_social = nombre_razon_social.text if nombre_razon_social is not None else 'No disponible'
                tipo_persona = tipo_persona.text if tipo_persona is not None else 'No disponible'
                direccion = direccion.text if direccion is not None else 'No disponible'
                telefono = telefono.text if telefono is not None else 'No disponible'
                email = email.text if email is not None else 'No disponible'
                actividad_economica = actividad_economica.text if actividad_economica is not None else 'No disponible'

                # Guardar en la base de datos
                informacion_terceros = InformacionTerceros(
                    identificacion=identificacion,
                    nombre_razon_social=nombre_razon_social,
                    tipo_persona=tipo_persona,
                    direccion=direccion,
                    telefono=telefono,
                    email=email,
                    actividad_economica=actividad_economica
                )
                db.session.add(informacion_terceros)

            # Commit after processing
            db.session.commit()

    except Exception as e:
        print(f"Error al procesar el archivo XML: {str(e)}")
        db.session.rollback()  # Rollback changes if an error occurs

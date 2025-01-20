import xml.etree.ElementTree as ET
from flask import Blueprint, request, jsonify, render_template
from io import BytesIO
from app import db
from app.models.models import (
    Empresa, InformacionTerceros, Facturacion, InvoiceLine,
    DatosXML, FacturacionXML, ProductosXML, ImpuestosXML, NotasXML
)
import json
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Crear el Blueprint
xml_upload_bp = Blueprint('xml_upload', __name__)

@xml_upload_bp.route('/upload', methods=['GET', 'POST'])
def upload_xml():
    if request.method == 'POST':
        try:
            if 'xml_file' not in request.files:
                logger.warning('No se seleccionó archivo')
                return render_template('upload_xml.html', 
                                     error='No se seleccionó ningún archivo',
                                     datos=None, facturacion=None, 
                                     productos=None, impuestos=None, notas=None)
            
            file = request.files['xml_file']
            if file.filename == '':
                logger.warning('Nombre de archivo vacío')
                return render_template('upload_xml.html', 
                                     error='No se seleccionó un archivo',
                                     datos=None, facturacion=None, 
                                     productos=None, impuestos=None, notas=None)

            # Procesar archivo
            file_content = BytesIO(file.read())
            datos, facturacion, productos, impuestos, notas = parse_xml(file_content)
            
            # Procesar datos directamente sin JSON intermedio
            datos_clean = [{
                'company_id': str(d['company_id']).strip(),
                'registration_name': str(d['registration_name']).strip(),
                'tax_level_code': str(d['tax_level_code']).strip(),
                'address': str(d['address']).strip(),
                'city_name': str(d['city_name']).strip(),
                'country_subentity': str(d['country_subentity']).strip(),
                'country_subentity_code': str(d['country_subentity_code']).strip(),
                'country': str(d['country']).strip(),
                'country_name': str(d['country_name']).strip(),
                'telephone': str(d['telephone']).strip(),
                'electronic_mail': str(d['electronic_mail']).strip()
            } for d in datos] if datos else []

            facturacion_clean = [{
                'document_id': str(f['document_id']).strip(),
                'uuid': str(f['uuid']).strip(),
                'issue_date': datetime.strptime(f['issue_date'], '%Y-%m-%d').strftime('%Y-%m-%d'),
                'issue_time': str(f['issue_time']).strip(),
                'due_date': datetime.strptime(f['due_date'], '%Y-%m-%d').strftime('%Y-%m-%d'),
                'invoice_type_code': str(f['invoice_type_code']).strip(),
                'document_currency_code': str(f['document_currency_code']).strip(),
                'line_count_numeric': int(float(f['line_count_numeric'])),
                'supplier_id': str(f['supplier_id']).strip(),
                'customer_id': str(f['customer_id']).strip()
            } for f in facturacion] if facturacion else []

            productos_clean = [{
                'nro': int(p['nro']),
                'codigo': str(p['codigo']).strip(),
                'descripcion': str(p['descripcion']).strip(),
                'um': str(p['um']).strip(),
                'cantidad': float(p['cantidad']),
                'precio_unitario': float(p['precio_unitario']),
                'precio_venta': float(p['precio_venta']),
                'descuento_detalle': float(p['descuento_detalle']),
                'recargo_detalle': float(p['recargo_detalle']),
                'iva': float(p['iva']),
                'inc': float(p['inc'])
            } for p in productos] if productos else []

            # Procesar impuestos sin variable adicional
            impuestos_clean = [{
                'taxable_amount': float(imp['taxable_amount']),
                'tax_amount': float(imp['tax_amount']),
                'tax_percent': float(imp['tax_percent']),
                'tax_scheme_id': str(imp['tax_scheme_id']).strip(),
                'tax_scheme_name': str(imp['tax_scheme_name']).strip()
            } for imp in impuestos] if impuestos else []

            notas_clean = [{'nota': str(n['nota']).strip()} for n in notas] if notas else []

            return render_template('upload_xml.html',
                                datos=datos_clean,
                                facturacion=facturacion_clean,
                                productos=productos_clean,
                                impuestos=impuestos_clean,
                                notas=notas_clean,
                                success='XML procesado correctamente')

        except Exception as e:
            logger.error(f"Error durante el procesamiento: {str(e)}")
            return render_template('upload_xml.html', 
                                error=f'Error durante el procesamiento: {str(e)}',
                                datos=None, facturacion=None, 
                                productos=None, impuestos=None, notas=None)

    return render_template('upload_xml.html',
                         datos=None, facturacion=None, 
                         productos=None, impuestos=None, notas=None)
    
        
@xml_upload_bp.route('/export_data', methods=['POST'])
def export_data():
    try:
        # Log detallado del request
        logger.debug("----- Inicio Request -----")
        logger.debug(f"Headers: {dict(request.headers)}")
        logger.debug(f"Content-Type: {request.content_type}")

        # Validar Content-Type
        if not request.content_type or 'application/json' not in request.content_type:
            logger.error(f'Content-Type inválido: {request.content_type}')
            return jsonify({
                'status': 'error',
                'message': f'Content-Type debe ser application/json. Recibido: {request.content_type}'
            }), 400

        # Obtener datos JSON con manejo de errores mejorado
        try:
            data = request.get_json(force=True)  # force=True para forzar parseo JSON
            logger.debug(f"Datos recibidos: {data}")

            if not data:
                logger.error("Datos JSON vacíos")
                return jsonify({
                    'status': 'error',
                    'message': 'No se recibieron datos JSON'
                }), 400
        except json.JSONDecodeError as e:
            logger.error(f"Error procesando JSON: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Error en el formato JSON: {str(e)}'
            }), 400

        # Extraer datos
        datos = data.get('datos', [])
        facturacion = data.get('facturacion', [])
        productos = data.get('productos', [])
        impuestos = data.get('impuestos', [])
        notas = data.get('notas', [])

        # Validar datos requeridos
        if not all([datos, facturacion, productos, impuestos, notas]):
            campos_faltantes = [k for k, v in {
                'datos': datos,
                'facturacion': facturacion,
                'productos': productos,
                'impuestos': impuestos,
                'notas': notas
            }.items() if not v]
            logger.warning(f'Campos faltantes: {campos_faltantes}')
            return jsonify({
                'status': 'error',
                'message': f'Faltan datos requeridos: {", ".join(campos_faltantes)}'
            }), 400

        logger.info('Iniciando transacción en BD')
        
        try:
            # Guardar datos de empresa y terceros
            for dato in datos:
                try:
                    # Verificar si es emisor o receptor
                    es_emisor = dato['company_id'] == facturacion[0]['supplier_id']
                    
                    # Crear y guardar empresa
                    empresa = Empresa(
                        company_id=dato['company_id'],
                        registration_name=dato['registration_name'],
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
                    logger.info(f"Empresa registrada: {dato['registration_name']}")

                    # Crear y guardar tercero
                    tercero = InformacionTerceros(
                        company_id=dato['company_id'],
                        registration_name=dato['registration_name'],
                        tax_level_code=dato['tax_level_code'],
                        address=dato['address'],
                        city_name=dato['city_name'],
                        country_subentity=dato['country_subentity'],
                        country_subentity_code=dato['country_subentity_code'],
                        country=dato['country'],
                        country_name=dato['country_name'],
                        telephone=dato['telephone'],
                        electronic_mail=dato['electronic_mail'],
                        tipo='EMISOR' if es_emisor else 'RECEPTOR'
                    )
                    db.session.add(tercero)
                    logger.info(f"Tercero registrado: {dato['registration_name']} como {tercero.tipo}")

                except KeyError as ke:
                    logger.error(f'Campo requerido faltante en datos: {ke}')
                    raise ValueError(f'Campo requerido faltante en datos: {ke}')

            # Guardar documentos XML
            for dato in datos:
                nuevo_dato = DatosXML(**dato)
                db.session.add(nuevo_dato)
                logger.debug(f"DatosXML guardados: {dato['registration_name']}")

            for factura in facturacion:
                nueva_factura = FacturacionXML(**factura)
                db.session.add(nueva_factura)
                logger.debug(f"FacturacionXML guardada: {factura['document_id']}")

            for producto in productos:
                nuevo_producto = ProductosXML(**producto)
                db.session.add(nuevo_producto)
                logger.debug(f"ProductoXML guardado: {producto['descripcion']}")

            for impuesto in impuestos:
                nuevo_impuesto = ImpuestosXML(**impuesto)
                db.session.add(nuevo_impuesto)
                logger.debug(f"ImpuestoXML guardado")

            for nota in notas:
                nueva_nota = NotasXML(**nota)
                db.session.add(nueva_nota)
                logger.debug(f"NotaXML guardada")

            # Confirmar transacción
            db.session.commit()
            logger.info('Transacción completada exitosamente')
            
            return jsonify({
                'status': 'success',
                'message': 'Datos exportados correctamente'
            })

        except Exception as db_error:
            db.session.rollback()
            logger.error(f"Error en BD: {str(db_error)}")
            raise

    except Exception as e:
        logger.error(f"Error general: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error al guardar en la base de datos: {str(e)}'
        }), 500

def parse_xml(file_content):
    """Parsea el archivo XML y extrae los datos necesarios"""
    namespaces = {
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
        'sts': 'dian:gov:co:facturaelectronica:Structures-2-1'
    }

    try:
        tree = ET.parse(file_content)
        root = tree.getroot()
        
        datos = []
        facturacion = []
        productos = []
        impuestos = []
        notas = []

        description_node = root.find('.//cbc:Description', namespaces=namespaces)
        if description_node is not None and description_node.text:
            inner_xml_content = description_node.text.strip()
            logger.debug("Contenido CDATA extraído")

            try:
                inner_tree = ET.ElementTree(ET.fromstring(inner_xml_content))
                inner_root = inner_tree.getroot()

                # Extraer información de emisor y receptor
                supplier_party = inner_root.find('cac:AccountingSupplierParty/cac:Party', namespaces=namespaces)
                supplier_info = extract_party_info(supplier_party, namespaces)
                datos.append(supplier_info)
                logger.debug(f"Información del emisor extraída: {supplier_info['registration_name']}")

                customer_party = inner_root.find('cac:AccountingCustomerParty/cac:Party', namespaces=namespaces)
                customer_info = extract_party_info(customer_party, namespaces)
                datos.append(customer_info)
                logger.debug(f"Información del receptor extraída: {customer_info['registration_name']}")

                # Extraer información de facturación
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
                logger.debug(f"Información de facturación extraída: {facturacion_data['document_id']}")

                # Extraer productos
                for line in inner_root.findall('.//cac:InvoiceLine', namespaces=namespaces):
                    producto = {
                        'nro': line.findtext('cbc:ID', namespaces=namespaces),
                        'codigo': line.findtext('.//cac:StandardItemIdentification/cbc:ID', namespaces=namespaces),
                        'descripcion': line.findtext('.//cbc:Description', namespaces=namespaces),
                        'um': line.findtext('.//cbc:BaseQuantity', namespaces=namespaces),
                        'cantidad': line.findtext('.//cbc:InvoicedQuantity', namespaces=namespaces),
                        'precio_unitario': line.findtext('.//cbc:PriceAmount', namespaces=namespaces),
                        'precio_venta': line.findtext('.//cbc:LineExtensionAmount', namespaces=namespaces),
                        'descuento_detalle': '0.00',
                        'recargo_detalle': '0.00',
                        'iva': line.findtext('.//cac:TaxTotal/cbc:TaxAmount', namespaces=namespaces) or '0.00',
                        'inc': '0.00'
                    }
                    productos.append(producto)
                    logger.debug(f"Producto extraído: {producto['descripcion']}")

                # Extraer impuestos
                for tax_total in inner_root.findall('.//cac:TaxTotal', namespaces=namespaces):
                    for tax_subtotal in tax_total.findall('.//cac:TaxSubtotal', namespaces=namespaces):
                        impuesto = {
                            'taxable_amount': tax_subtotal.findtext('cbc:TaxableAmount', namespaces=namespaces),
                            'tax_amount': tax_subtotal.findtext('cbc:TaxAmount', namespaces=namespaces),
                            'tax_percent': tax_subtotal.findtext('.//cbc:Percent', namespaces=namespaces),
                            'tax_scheme_id': tax_subtotal.findtext('.//cac:TaxScheme/cbc:ID', namespaces=namespaces),
                            'tax_scheme_name': tax_subtotal.findtext('.//cac:TaxScheme/cbc:Name', namespaces=namespaces)
                        }
                        impuestos.append(impuesto)
                        logger.debug(f"Impuesto extraído: {impuesto['tax_scheme_name']}")

                # Extraer notas
                for note in inner_root.findall('.//cbc:Note', namespaces=namespaces):
                    if note is not None and note.text:
                        nota = {'nota': note.text.strip()}
                        notas.append(nota)
                        logger.debug("Nota extraída")

            except ET.ParseError as e:
                logger.error(f"Error al parsear XML interno: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Error inesperado: {str(e)}")
                raise
        else:
            logger.warning("Nodo Description no encontrado o vacío")

        return datos, facturacion, productos, impuestos, notas

    except Exception as e:
        logger.error(f"Error en parse_xml: {str(e)}")
        raise

def extract_party_info(party, namespaces):
    """
    Extrae información de una entidad (emisor/receptor) del XML.
    
    Args:
        party: Nodo XML con la información de la entidad
        namespaces: Diccionario con los namespaces del XML
    
    Returns:
        dict: Diccionario con la información extraída
    """
    # Valores por defecto si no hay datos
    default_values = {
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

    if party is None:
        logger.warning("Nodo party no encontrado, retornando valores por defecto")
        return default_values

    try:
        # Extraer información básica
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

        # Reemplazar None por valor por defecto
        for key, value in info.items():
            if value is None:
                info[key] = default_values[key]
                logger.debug(f"Valor no encontrado para {key}, usando valor por defecto: {default_values[key]}")

        logger.debug(f"Información extraída para {info['registration_name']}: {info}")
        return info

    except Exception as e:
        logger.error(f"Error extrayendo información: {str(e)}")
        return default_values

def print_data(datos, facturacion, productos, impuestos, notas):
    """
    Imprime los datos extraídos del XML usando el logger.
    
    Args:
        datos: Lista de diccionarios con información de terceros
        facturacion: Lista de diccionarios con información de facturación
        productos: Lista de diccionarios con información de productos
        impuestos: Lista de diccionarios con información de impuestos
        notas: Lista de diccionarios con notas
    """
    try:
        logger.debug("=== DATOS EXTRAÍDOS DEL XML ===")
        
        if datos:
            logger.debug("\n=== INFORMACIÓN DE TERCEROS ===")
            for d in datos:
                logger.debug(f"Nombre: {d.get('registration_name', 'N/A')}")
                logger.debug(f"ID: {d.get('company_id', 'N/A')}")
                logger.debug("-------------------------")
        
        if facturacion:
            logger.debug("\n=== INFORMACIÓN DE FACTURACIÓN ===")
            for f in facturacion:
                logger.debug(f"Documento: {f.get('document_id', 'N/A')}")
                logger.debug(f"Fecha: {f.get('issue_date', 'N/A')}")
                logger.debug("-------------------------")
        
        if productos:
            logger.debug("\n=== PRODUCTOS ===")
            for p in productos:
                logger.debug(f"Descripción: {p.get('descripcion', 'N/A')}")
                logger.debug(f"Cantidad: {p.get('cantidad', 'N/A')}")
                logger.debug(f"Precio: {p.get('precio_unitario', 'N/A')}")
                logger.debug("-------------------------")
        
        if impuestos:
            logger.debug("\n=== IMPUESTOS ===")
            for i in impuestos:
                logger.debug(f"Tipo: {i.get('tax_scheme_name', 'N/A')}")
                logger.debug(f"Monto: {i.get('tax_amount', 'N/A')}")
                logger.debug("-------------------------")
        
        if notas:
            logger.debug("\n=== NOTAS ===")
            for n in notas:
                logger.debug(f"Nota: {n.get('nota', 'N/A')}")
                logger.debug("-------------------------")
                
    except Exception as e:
        logger.error(f"Error al imprimir datos: {str(e)}")

def save_to_db(datos, facturacion, productos, impuestos, notas):
    """
    Guarda los datos en la base de datos usando los modelos antiguos y nuevos.
    
    Args:
        datos: Lista de diccionarios con información de terceros
        facturacion: Lista de diccionarios con información de facturación
        productos: Lista de diccionarios con información de productos
        impuestos: Lista de diccionarios con información de impuestos
        notas: Lista de diccionarios con notas
    """
    try:
        # Guardar en modelos antiguos
        logger.info("Iniciando guardado en modelos antiguos")
        for dato in datos:
            empresa = InformacionTerceros(**dato)
            db.session.add(empresa)
            logger.debug(f"Guardado tercero: {dato['registration_name']}")

        for factura in facturacion:
            fact = Facturacion(**factura)
            db.session.add(fact)
            logger.debug(f"Guardada factura: {factura['document_id']}")

        for producto in productos:
            line = InvoiceLine(**producto)
            db.session.add(line)
            logger.debug(f"Guardado producto: {producto['descripcion']}")

        # Guardar en nuevos modelos XML
        logger.info("Iniciando guardado en modelos XML")
        for dato in datos:
            nuevo_dato = DatosXML(**dato)
            db.session.add(nuevo_dato)
            logger.debug(f"Guardado XML tercero: {dato['registration_name']}")

        for factura in facturacion:
            nueva_factura = FacturacionXML(**factura)
            db.session.add(nueva_factura)
            logger.debug(f"Guardada XML factura: {factura['document_id']}")

        for producto in productos:
            nuevo_producto = ProductosXML(**producto)
            db.session.add(nuevo_producto)
            logger.debug(f"Guardado XML producto: {producto['descripcion']}")

        for impuesto in impuestos:
            nuevo_impuesto = ImpuestosXML(**impuesto)
            db.session.add(nuevo_impuesto)
            logger.debug(f"Guardado XML impuesto: {impuesto['tax_scheme_name']}")

        for nota in notas:
            nueva_nota = NotasXML(**nota)
            db.session.add(nueva_nota)
            logger.debug(f"Guardada XML nota")

        db.session.commit()
        logger.info("Datos guardados exitosamente")
        return True

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al guardar en BD: {str(e)}")
        raise

    finally:
        db.session.close()
        logger.debug("Sesión de BD cerrada")
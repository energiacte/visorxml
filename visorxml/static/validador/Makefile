SCHEMA=DatosEnergeticosDelEdificioSchema20.xsd
XMLFILE?=EjemploResidencial.xml
all:
	xmllint --noout --dtdvalid http://www.w3.org/2001/XMLSchema.dtd ${SCHEMA}
	xmllint --noout --schema ${SCHEMA} EjemploResidencial.xml
	xmllint --noout --schema ${SCHEMA} EjemploTerciario.xml

validateXSD:
	xmllint --noout --dtdvalid http://www.w3.org/2001/XMLSchema.dtd ${SCHEMA}

validateXML:
	xmllint --noout --schema ${SCHEMA} ${XMLFILE}

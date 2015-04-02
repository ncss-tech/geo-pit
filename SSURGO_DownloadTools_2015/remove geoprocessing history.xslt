<?xml version="1.0" encoding="UTF-8"?>
<!-- Processes ArcGIS metadata to remove empty XML elements to avoid exporting and validation errors. -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" >
	<xsl:output method="xml" version="1.0" encoding="UTF-8" indent="yes" omit-xml-declaration="no" />

	<!-- start processing all nodes and attributes in the XML document -->
	<!-- any CDATA blocks in the original XML will be lost because they can't be handled by XSLT -->
	<xsl:template match="/">
		<xsl:apply-templates select="node() | @*" />
	</xsl:template>

	<!-- copy all nodes and attributes in the XML document -->
	<xsl:template match="node() | @*" priority="0">
		<xsl:copy>
			<xsl:apply-templates select="node() | @*" />
		</xsl:copy>
	</xsl:template>

	<!-- templates below override the default template above that copies all nodes and attributes -->
	
	<!-- exclude geoprocessing history -->
	<xsl:template match="/metadata/Esri/DataProperties/lineage" priority="1">
	</xsl:template>

</xsl:stylesheet>

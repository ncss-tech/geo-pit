#-------------------------------------------------------------------------------
# Name:        Pedon_Excel_Conversion_S123
# Purpose:
#
# Author:      Alena.Stephens
#
# Created:     13/11/2018
# Copyright:   (c) Alena.Stephens 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------


import arcpy
import os

arcpy.env.overwriteOutput = True


#Input File Geodatabase

workspace = arcpy.GetParameterAsText(0)
#arcpy.env.workspace = workspace

#Output Folder
out_folder = arcpy.GetParameterAsText(1)
arcpy.env.workspace = out_folder
#Input Files
#Transcript_Description
#ped_repeat
#redex_repeat
#veggie_repeat
#diag_horz_repeat
#comp_repeat


#inFC = arcpy.GetParameterAsText (0) # Input Feature Class
#out_xls = arcpy.GetParametersAsText (1) #Output Excel Name (add xls extension)

#Table to Excel
#arcpy.TableToExcel_conversion(inFC, out_xls)


arcpy.TableToExcel_conversion("Transcript_Description", "Transcript_Description.xls")
arcpy.TableToExcel_conversion("ped_repeat", "ped_repeat.xls")
arcpy.TableToExcel_conversion("redex_repeat", "redex_repeat.xls")
arcpy.TableToExcel_conversion("veggie_repeat", "veggie_repeat.xls")
arcpy.TableToExcel_conversion("diag_horz_repeat", "diag_horz_repeat.xls")
arcpy.TableToExcel_conversion("comp_repeat", "comp_repeat.xls")

#arcpy.TableToExcel_conversion("Transcript_Description", "Transcript_Description.csv")
#arcpy.TableToExcel_conversion("ped_repeat", "ped_repeat.csv")
#arcpy.TableToExcel_conversion("redex_repeat", "redex_repeat.csv")
#arcpy.TableToExcel_conversion("veggie_repeat", "veggie_repeat.csv")
#arcpy.TableToExcel_conversion("diag_horz_repeat", "diag_horz_repeat.csv")
#arcpy.TableToExcel_conversion("comp_repeat", "comp_repeat.csv")

#Merge All Excel worksheets into 1 workbook

print"Script Completed"
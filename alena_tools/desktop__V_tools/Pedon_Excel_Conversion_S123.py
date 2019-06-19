#-------------------------------------------------------------------------------
# Name:        Pedon_Excel_Conversion_S123
# Purpose:
#
# Author:      Alena.Stephens
#
# Created:     12/11/2018
# Copyright:   (c) Alena.Stephens 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#updated 6/17/2019

import arcpy
import os
import sys
import xlrd

#def force_restart_script():
#    python = sys.executable
#    os.excel(python, python, * sys.argv)

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

#Convert tables to excel if it exists
#if arcpy.Exists(workspace):
#arcpy.TableToExcel_conversion("Transcript_Description", "Transcript_Description.xls")
arcpy.TableToExcel_conversion(workspace+'\\'+"Transcript_Description", out_folder+"\\Transcript_Description.xls")
#arcpy.TableToExcel_conversion("comp_repeat", "comp_repeat.xls")
arcpy.TableToExcel_conversion(workspace+'\\'+"comp_repeat", out_folder+"\\comp_repeat.xls")
#arcpy.TableToExcel_conversion("diag_horz_repeat", "diag_horz_repeat.xls")
arcpy.TableToExcel_conversion(workspace+'\\'+"diag_horz_repeat", out_folder+"\\diag_horz_repeat.xls")
#arcpy.TableToExcel_conversion("ped_repeat", "ped_repeat.xls")
arcpy.TableToExcel_conversion(workspace+'\\'+"ped_repeat", out_folder+"\\ped_repeat.xls")
#arcpy.TableToExcel_conversion("pm_repeat", "pm_repeat.xls")
arcpy.TableToExcel_conversion(workspace+'\\'+"pm_repeat", out_folder+"\\pm_repeat.xls")
#arcpy.TableToExcel_conversion("redex_repeat", "redex_repeat.xls")
arcpy.TableToExcel_conversion(workspace+'\\'+"redex_repeat", out_folder+"\\redex_repeat.xls")
#arcpy.TableToExcel_conversion("rock_repeat_frag", "rock_repeat_frag.xls")
arcpy.TableToExcel_conversion(workspace+'\\'+"rock_repeat_frag", out_folder+"\\rock_repeat_frag.xls")
#arcpy.TableToExcel_conversion("slope_shape_repeat", "slope_shape_repeat.xls")
arcpy.TableToExcel_conversion(workspace+'\\'+"slope_shape_repeat", out_folder+"\\slope_shape_repeat.xls")
#arcpy.TableToExcel_conversion("structure_repeat", "structure_repeat.xls")
arcpy.TableToExcel_conversion(workspace+'\\'+"structure_repeat", out_folder+"\\structure_repeat.xls")
#arcpy.TableToExcel_conversion("veggie_repeat", "veggie_repeat.xls")
arcpy.TableToExcel_conversion(workspace+'\\'+"veggie_repeat", out_folder+"\\veggie_repeat.xls")

#arcpy.TableToExcel_conversion("Transcript_Description", "Transcript_Description.csv")
#arcpy.TableToExcel_conversion("ped_repeat", "ped_repeat.csv")
#arcpy.TableToExcel_conversion("redex_repeat", "redex_repeat.csv")
#arcpy.TableToExcel_conversion("veggie_repeat", "veggie_repeat.csv")
#arcpy.TableToExcel_conversion("diag_horz_repeat", "diag_horz_repeat.csv")
#arcpy.TableToExcel_conversion("comp_repeat", "comp_repeat.csv")

#Merge All Excel worksheets into 1 workbook

#def importallsheets(in_excel, workspace):
#    workbook = xlrd.open_workbook(in_excel)
#    sheets = [sheet.name for sheet in workbook.sheets()]

#    print('{} sheets found: {}'.format(len(sheets), ','.join(sheets)))
#    for sheet in sheets:
        # The out_table is based on the input excel file name
        # a underscore (_) separator followed by the sheet name
#        out_table = os.path.join(
#            out_gdb,
#            arcpy.ValidateTableName(
#                "{0}_{1}".format(os.path.basename(in_excel), sheet),
#                out_gdb))

#        print('Converting {} to {}'.format(sheet, out_table))

#if __name__ == '__main__':
#    importallsheets('C:\Workspace\s123\Transcript_Description.xls',
#                    out_folder)

print"Script Completed"

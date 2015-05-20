#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      charles.ferguson
#
# Created:     20/05/2015
# Copyright:   (c) charles.ferguson 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sys, os, arcpy

changeTbl = arcpy.GetParameterAsText(0)

arcpy.AddMessage(changeTbl)


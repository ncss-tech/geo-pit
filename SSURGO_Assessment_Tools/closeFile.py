#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Adolfo.Diaz
#
# Created:     11/01/2016
# Copyright:   (c) Adolfo.Diaz 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------

## ===================================================================================
class ExitError(Exception):
    pass

## ===================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        print msg

        #for string in msg.split('\n'):
            #Add a geoprocessing message (in case this is run as a tool)
        if severity == 0:
            arcpy.AddMessage(msg)

        elif severity == 1:
            arcpy.AddWarning(msg)

        elif severity == 2:
            arcpy.AddError("\n" + msg)

    except:
        pass

## ===================================================================================
def errorMsg():

    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        theMsg = "\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[1] + "\n\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[-1]
        AddMsgAndPrint(theMsg,2)
        print theMsg

    except:
        AddMsgAndPrint("Unhandled error in errorMsg method", 2)
        pass

## ===================================================================================
def closeFile(file):
    # This function will close a specific file if it is currently opened in windows
    # by killing its process ID (PID).  Takes in 1 argument: the file (path and name)
    # In python 3.0 or higher try using the psutil to obtain list of processes and IDs
    # and kill processes as well.

    try:
        import subprocess, signal

        fileName = os.path.basename(file)
        print file

        # command that will be passed
        # WMIC = Windows Management Instrumentation Command-line (command line and scripting interface)
        # PROCESS = list all currently running Processes
        # get "Caption,Commandline,Processid" properties from processes
        cmd = 'WMIC PROCESS get Caption,Commandline,Processid'

        # connect to all currently running window processes by executing a child program
        # through a new process using the Popen constructor
        # The shell argument (which defaults to False) specifies whether to use the shell as the program
        # to execute. If shell is True, it is recommended to pass args as a string rather than as a sequence.
        # The only time you need to specify shell=True on Windows is when the command you wish to execute is
        # built into the shell (e.g. dir or copy). You do not need shell=True to run a batch file or console-based executable.
        # I set it to true b/c 'WMIC PROCESS...etc' is built into the CMD.exe shell
        # subprocess.PIPE = Special value that can be used as the stdin, stdout or stderr argument to Popen and indicates
        # that a pipe to the standard stream should be opened.
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

        for line in proc.stdout:

            if str(line).find(file) > -1:

                # Capture the program, file path, PID
                # ['notepad.exe', '"C:\\Windows\\system32\\NOTEPAD.EXE"', 'C:\\Temp\\SuperfishCertificateCheck.txt', '4836']
                process = line.split()
                processID = int(process[len(process)-1])

                AddMsgAndPrint(fileName + " is currently open.  Automatically closing file!",2)
                time.sleep(2)

                try:
                    # Signals are an operating system feature that provide a means of notification of an event,
                    # and having it handled asynchronously.  Send Signal to the process ID.
                    os.kill(processID, signal.SIGTERM)

                    # terminate the Popen construct (should get rid of WMIC and cmd.exe processes)
                    proc.kill()
                    print "Fuck Yeah!"
                except:
                    proc.kill()
                    AddMsgAndPrint("\tCould not close file",2)
                    errorMsg()
                    return False

                del process
                print "Hec yeah"
                return True

        del fileName,cmd,proc
        return False

    except:
        errorMsg()
        return False

if __name__ == '__main__':
    import os,sys,time, traceback

    histogramFile = r'C:\Temp\scratch\SDJR  MLRA 103  Storden loam 16 to 22 percent slopes moderately eroded Histogram 10M.pdf'

    test = closeFile(histogramFile)
    time.sleep(3)

    print test
#    os.remove(histogramFile)

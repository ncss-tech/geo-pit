# Update.py - update hosted feature services by replacing the .SD file
#   and calling publishing (with overwrite) to update the feature service
#

import os, sys, time, string, random, traceback
import urllib2, urllib, json

import ConfigParser, ast

import mimetypes, gzip
from io import BytesIO

from xml.etree import ElementTree as ET
import arcpy


## ===================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        #print msg

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

    except:
        AddMsgAndPrint("Unhandled error in errorMsg method", 2)
        pass

## ===================================================================================

class AGOLHandler(object):

    def __init__(self, username, password, serviceName, folderName, proxyDict):

        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'User-Agent': ('updatehostedfeatureservice')
        }
        self.username = username
        self.password = password
        self.base_url = "https://www.arcgis.com/sharing/rest"
        self.proxyDict = proxyDict
        self.serviceName = serviceName
        self.token = self.getToken(username, password)
        self.itemID = self.findItem("Feature Service")
        self.SDitemID = self.findItem("Service Definition")
        self.folderName = folderName
        self.folderID = self.findFolder()

    def getToken(self, username, password, exp=60):
        """ Establish URL Token with AGOL
            URL tokens are a way to give users access permission for various Web resources."""

        referer = "http://www.arcgis.com/"
        query_dict = {'username': username,
                      'password': password,
                      'expiration': str(exp),
                      'client': 'referer',
                      'referer': referer,
                      'f': 'json'}

        # add 'generateToken' to base_url:
        token_url = '{}/generateToken'.format(self.base_url) # https://www.arcgis.com/sharing/rest/generateToken

        token_response = self.url_request(token_url, query_dict, request_type='POST', repeat=1)

        if "token" not in token_response:
            AddMsgAndPrint(token_response['error'],2)
            sys.exit()
        else:
            return token_response['token']

    def findItem(self, findType):
        """ Find the itemID of whats being updated
        """

        searchURL = self.base_url + "/search"

        query_dict = {'f': 'json',
                      'token': self.token,
                      'q': "title:\"" + self.serviceName + "\"AND owner:\"" +
                      self.username + "\" AND type:\"" + findType + "\""}

        jsonResponse = self.url_request(searchURL, query_dict, 'POST')

        if jsonResponse['total'] == 0:
            print("\nCould not find a service to update. Check the service name in the settings.ini")
            sys.exit()
        else:
            resultList = jsonResponse['results']
            for it in resultList:
                if it["title"] == self.serviceName:
                    print("found {} : {}").format(findType, it["id"])
                    return it["id"]

    def findFolder(self, folderName=None):
        """ Find the ID of the folder containing the service
        """

        if self.folderName == "None":
            return ""

        findURL = "{}/content/users/{}".format(self.base_url, self.username)

        query_dict = {'f': 'json',
                      'num': 1,
                      'token': self.token}

        jsonResponse = self.url_request(findURL, query_dict, 'POST')

        for folder in jsonResponse['folders']:
            if folder['title'] == self.folderName:
                return folder['id']

        print("\nCould not find the specified folder name provided in the settings.ini")
        print("-- If your content is in the root folder, change the folder name to 'None'")
        sys.exit()

    def upload(self, fileName, tags, description):
        """
         Overwrite the SD on AGOL with the new SD.
         This method uses 3rd party module: requests
        """

        updateURL = '{}/content/users/{}/{}/items/{}/update'.format(self.base_url, self.username,
                                                                    self.folderID, self.SDitemID)

        query_dict = {"filename": fileName,
                      "type": "Service Definition",
                      "title": self.serviceName,
                      "tags": tags,
                      "description": description,
                      "f": "json",
                      'multipart': 'true',
                      "token": self.token}

        details = {'filename': fileName}
        add_item_res = self.url_request(updateURL, query_dict, "POST", "", details)

        itemPartJSON = self._add_part(fileName, add_item_res['id'], "Service Definition")

        if "success" in itemPartJSON:
            itemPartID = itemPartJSON['id']

            commit_response = self.commit(itemPartID)

            # valid states: partial | processing | failed | completed
            status = 'processing'
            while status == 'processing' or status == 'partial':
                status = self.item_status(itemPartID)['status']
                time.sleep(1.5)

            print("updated SD:   {}".format(itemPartID))
            return True

        else:
            print("\n.sd file not uploaded. Check the errors and try again.\n")
            print(itemPartJSON)
            sys.exit()

    def _add_part(self, file_to_upload, item_id, upload_type=None):
        """ Add the item to the portal in chunks.
        """

        def read_in_chunks(file_object, chunk_size=10000000):
            """Generate file chunks of 10MB"""
            while True:
                data = file_object.read(chunk_size)
                if not data:
                    break
                yield data

        url = '{}/content/users/{}/items/{}/addPart'.format(self.base_url, self.username, item_id)

        with open(file_to_upload, 'rb') as f:
            for part_num, piece in enumerate(read_in_chunks(f), start=1):
                title = os.path.basename(file_to_upload)
                files = {"file": {"filename": file_to_upload, "content": piece}}
                params = {
                    'f': "json",
                    'token': self.token,
                    'partNum': part_num,
                    'title': title,
                    'itemType': 'file',
                    'type': upload_type
                }

                request_data, request_headers = self.multipart_request(params, files)
                resp = self.url_request(url, request_data, "MULTIPART", request_headers)

        return resp

    def item_status(self, item_id, jobId=None):
        """ Gets the status of an item.
        Returns:
            The item's status. (partial | processing | failed | completed)
        """

        url = '{}/content/users/{}/items/{}/status'.format(self.base_url, self.username, item_id)
        parameters = {'token': self.token,
                      'f': 'json'}

        if jobId:
            parameters['jobId'] = jobId

        return self.url_request(url, parameters)

    def commit(self, item_id):
        """ Commits an item that was uploaded as multipart
        """

        url = '{}/content/users/{}/items/{}/commit'.format(self.base_url, self.username, item_id)
        parameters = {'token': self.token,
                      'f': 'json'}

        return self.url_request(url, parameters)

    def publish(self):
        """ Publish the existing SD on AGOL (it will be turned into a Feature Service)
        """

        publishURL = '{}/content/users/{}/publish'.format(self.base_url, self.username)

        query_dict = {'itemID': self.SDitemID,
                      'filetype': 'serviceDefinition',
                      'overwrite': 'true',
                      'f': 'json',
                      'token': self.token}

        jsonResponse = self.url_request(publishURL, query_dict, 'POST')
        try:
            if 'jobId' in jsonResponse['services'][0]:
                jobID = jsonResponse['services'][0]['jobId']

                # valid states: partial | processing | failed | completed
                status = 'processing'
                print("Checking the status of publish..")
                while status == 'processing' or status == 'partial':
                    status = self.item_status(self.SDitemID, jobID)['status']
                    print("  {}".format(status))
                    time.sleep(2)

                if status == 'completed':
                    print("item finished published")
                    return jsonResponse['services'][0]['serviceItemId']
                if status == 'failed':
                    raise("Status of publishing returned FAILED.")

        except Exception as e:
            print("Problem trying to check publish status. Might be further errors.")
            print("Returned error Python:\n   {}".format(e))
            print("Message from publish call:\n  {}".format(jsonResponse))
            print(" -- quit --")
            sys.exit()


    def enableSharing(self, newItemID, everyone, orgs, groups):
        """ Share an item with everyone, the organization and/or groups
        """

        shareURL = '{}/content/users/{}/{}/items/{}/share'.format(self.base_url, self.username,
                                                                  self.folderID, newItemID)

        if groups is None:
            groups = ''

        query_dict = {'f': 'json',
                      'everyone': everyone,
                      'org': orgs,
                      'groups': groups,
                      'token': self.token}

        jsonResponse = self.url_request(shareURL, query_dict, 'POST')

        print("successfully shared...{}...".format(jsonResponse['itemId']))

    def url_request(self, in_url, request_parameters, request_type='GET',
                    additional_headers=None, files=None, repeat=0):
        """
        Make a request to the portal, provided a portal URL
        and request parameters.
        returns portal response in JSON format

        Arguments:
            in_url -- portal url -- https://www.arcgis.com/sharing/rest/generateToken
            request_parameters -- dictionary of request parameters:
                {'client': 'referer',
                'expiration': '60',
                'f': 'json',
                'password': 'somePassWord',
                'referer': 'http://www.arcgis.com/',
                'username': 'someUserName'}
            request_type -- HTTP verb (default: GET, POST will be used for backups):
                GET - Requests data from a specified resource
                POST - Submits data to be processed to a specified resource
                (for more info - https://www.w3schools.com/tags/ref_httpmethods.asp)
            additional_headers -- any headers to pass along with the request.
            files -- any files to send.
            repeat -- repeat the request up to this number of times.

        Returns:
            dictionary of response from portal instance.
        """

        # --------------------------------Send request to AGOL - backups will be sent via POST
        try:
            if request_type == 'GET':
                req = urllib2.Request('?'.join((in_url, urllib.urlencode(request_parameters))))
            elif request_type == 'MULTIPART':
                req = urllib2.Request(in_url, request_parameters)
            else:
                req = urllib2.Request(
                    in_url, urllib.urlencode(request_parameters), self.headers)

        except urllib2.HTTPError, e:
            checksLogger.error('HTTPError = ' + str(e.code))
        except urllib2.URLError, e:
            checksLogger.error('URLError = ' + str(e.reason))
        except httplib.HTTPException, e:
            checksLogger.error('HTTPException')
        except:
            errorMsg()

        # --------------------------------------headers and proxyDict Not used in AGOL backups
        if additional_headers:
            for key, value in list(additional_headers.items()):
                req.add_header(key, value)

        req.add_header('Accept-encoding', 'gzip')

        if self.proxyDict:
            p = urllib2.ProxyHandler(self.proxyDict)
            auth = urllib2.HTTPBasicAuthHandler()
            opener = urllib2.build_opener(p, auth, urllib2.HTTPHandler)
            urllib2.install_opener(opener)

        # ----------open the AGOL request, which will be returned as string or a Request object
        response = urllib2.urlopen(req)

        # unzip the response if needed else just read it
        if response.info().get('Content-Encoding') == 'gzip':
            buf = BytesIO(response.read())
            with gzip.GzipFile(fileobj=buf) as gzip_file:
                response_bytes = gzip_file.read()
        else:
            response_bytes = response.read()   # returns a dict but in string format.

        response_text = response_bytes.decode('UTF-8')  # decode the response (not really necessary)
        response_json = json.loads(response_text)       # returns 3 item dict

        # --------------------------------------------------return valid response in JSON format
        if not response_json or "error" in response_json:
            rerun = False
            if repeat > 0:
                repeat -= 1
                rerun = True

            # response was invalid; re-call the url_request subfunction
            if rerun:
                AddMsgAndPrint("ArcGIS Online request Failed.  Trying Again!",2)
                time.sleep(2)
                response_json = self.url_request(
                    in_url, request_parameters, request_type,
                    additional_headers, files, repeat)

        return response_json
        """{u'expires': 1520368134822L,
            u'ssl': False,
            u'token': u'O0Rqq08Bl7q8GLsmEOxU3sStN3uC2ZtwAC-WCB9NazkAxhu83IlKjBXqnjzV1Rjy1H3q0oBVebSuu-dcdbCgvhXF8316m9WtI8CSWQAZzpYInuZqvPfabVZJ2nuQAsKCOmLbbcbh-IdPjSIeZBhMpQ..'}"""

    def multipart_request(self, params, files):
        """ Uploads files as multipart/form-data. files is a dict and must
            contain the required keys "filename" and "content". The "mimetype"
            value is optional and if not specified will use mimetypes.guess_type
            to determine the type or use type application/octet-stream. params
            is a dict containing the parameters to be passed in the HTTP
            POST request.

            content = open(file_path, "rb").read()
            files = {"file": {"filename": "some_file.sd", "content": content}}
            params = {"f": "json", "token": token, "type": item_type,
                      "title": title, "tags": tags, "description": description}
            data, headers = multipart_request(params, files)
            """
        # Get mix of letters and digits to form boundary.
        letters_digits = "".join(string.digits + string.ascii_letters)
        boundary = "----WebKitFormBoundary{}".format("".join(random.choice(letters_digits) for i in range(16)))
        file_lines = []
        # Parse the params and files dicts to build the multipart request.
        for name, value in params.iteritems():
            file_lines.extend(("--{}".format(boundary),
                               'Content-Disposition: form-data; name="{}"'.format(name),
                               "", str(value)))
        for name, value in files.items():
            if "filename" in value:
                filename = value.get("filename")
            else:
                raise Exception("The filename key is required.")
            if "mimetype" in value:
                mimetype = value.get("mimetype")
            else:
                mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            if "content" in value:
                file_lines.extend(("--{}".format(boundary),
                                   'Content-Disposition: form-data; name="{}"; filename="{}"'.format(name, filename),
                                   "Content-Type: {}".format(mimetype), "",
                                   (value.get("content"))))
            else:
                raise Exception("The content key is required.")
        # Create the end of the form boundary.
        file_lines.extend(("--{}--".format(boundary), ""))

        request_data = "\r\n".join(file_lines)
        request_headers = {"Content-Type": "multipart/form-data; boundary={}".format(boundary),
                           "Content-Length": str(len(request_data))}
        return request_data, request_headers


def makeSD(MXD, serviceName, tempDir, outputSD, maxRecords, tags, summary):
    """ create a draft SD and modify the properties to overwrite an existing FS
    """

    arcpy.env.overwriteOutput = True
    # All paths are built by joining names to the tempPath
    SDdraft = os.path.join(tempDir, "tempdraft.sddraft")
    newSDdraft = os.path.join(tempDir, "updatedDraft.sddraft")

    # Check the MXD for summary and tags, if empty, push them in.
    try:
        mappingMXD = arcpy.mapping.MapDocument(MXD)
        if mappingMXD.tags == "":
            mappingMXD.tags = tags
            mappingMXD.save()
        if mappingMXD.summary == "":
            mappingMXD.summary = summary
            mappingMXD.save()
    except IOError:
        print("IOError on save, do you have the MXD open? Summary/tag info not pushed to MXD, publishing may fail.")

    arcpy.mapping.CreateMapSDDraft(MXD, SDdraft, serviceName, "MY_HOSTED_SERVICES")

    # Read the contents of the original SDDraft into an xml parser
    doc = ET.parse(SDdraft)

    root_elem = doc.getroot()
    if root_elem.tag != "SVCManifest":
        raise ValueError("Root tag is incorrect. Is {} a .sddraft file?".format(SDDraft))

    # The following 6 code pieces modify the SDDraft from a new MapService
    # with caching capabilities to a FeatureService with Query,Create,
    # Update,Delete,Uploads,Editing capabilities as well as the ability
    # to set the max records on the service.
    # The first two lines (commented out) are no longer necessary as the FS
    # is now being deleted and re-published, not truly overwritten as is the
    # case when publishing from Desktop.
    # The last three pieces change Map to Feature Service, disable caching
    # and set appropriate capabilities. You can customize the capabilities by
    # removing items.
    # Note you cannot disable Query from a Feature Service.

    # doc.find("./Type").text = "esriServiceDefinitionType_Replacement"
    # doc.find("./State").text = "esriSDState_Published"

    # Change service type from map service to feature service
    for config in doc.findall("./Configurations/SVCConfiguration/TypeName"):
        if config.text == "MapServer":
            config.text = "FeatureServer"

    # Turn off caching
    for prop in doc.findall("./Configurations/SVCConfiguration/Definition/" +
                            "ConfigurationProperties/PropertyArray/" +
                            "PropertySetProperty"):
        if prop.find("Key").text == 'isCached':
            prop.find("Value").text = "false"
        if prop.find("Key").text == 'maxRecordCount':
            prop.find("Value").text = maxRecords

    # Turn on feature access capabilities
    for prop in doc.findall("./Configurations/SVCConfiguration/Definition/Info/PropertyArray/PropertySetProperty"):
        if prop.find("Key").text == 'WebCapabilities':
            prop.find("Value").text = "Query,Create,Update,Delete,Uploads,Editing"

    # Add the namespaces which get stripped, back into the .SD
    root_elem.attrib["xmlns:typens"] = 'http://www.esri.com/schemas/ArcGIS/10.1'
    root_elem.attrib["xmlns:xs"] = 'http://www.w3.org/2001/XMLSchema'

    # Write the new draft to disk
    with open(newSDdraft, 'w') as f:
        doc.write(f, 'utf-8')

    # Analyze the service
    analysis = arcpy.mapping.AnalyzeForSD(newSDdraft)

    if analysis['errors'] == {}:
        # Stage the service
        arcpy.StageService_server(newSDdraft, outputSD)
        print("Created {}".format(outputSD))

    else:
        # If the sddraft analysis contained errors, display them and quit.
        print("Errors in analyze: \n {}".format(analysis['errors']))
        sys.exit()


if __name__ == "__main__":

    MXD = arcpy.GetParameterAsText(0)
    serviceName = arcpy.GetParameterAsText(1)
    inputUsername = arcpy.GetParameterAsText(2)   # AGOL Credentials - Username
    inputPswd = arcpy.GetParameterAsText(3)       # AGOL Password - Password

    print("Starting Feature Service publish process")

    # Find and gather settings from the ini file
    localPath = sys.path[0]
    settingsFile = os.path.join(localPath, "settings.ini")

    # Check if .ini file exists
    if os.path.isfile(settingsFile):
        config = ConfigParser.ConfigParser() # parser for .ini files
        config.read(settingsFile)
    else:
        print("INI file not found. \nMake sure a valid 'settings.ini' file exists in the same directory as this script.")
        sys.exit()

##    # AGOL Credentials
##    inputUsername = config.get('AGOL', 'USER')
##    inputPswd = config.get('AGOL', 'PASS')

    # --------------------------------------------------- get Feature Service Info from .ini file
    #MXD = config.get('FS_INFO', 'MXD')
    #serviceName = config.get('FS_INFO', 'SERVICENAME')
    folderName = config.get('FS_INFO', 'FOLDERNAME')
    tags = config.get('FS_INFO', 'TAGS')
    summary = config.get('FS_INFO', 'DESCRIPTION')
    maxRecords = config.get('FS_INFO', 'MAXRECORDS')

    # --------------------------------------------------- get Feature Service Share settings: everyone, org, groups from .ini file
    shared = False
    #shared = config.get('FS_SHARE', 'SHARE')
    everyone = config.get('FS_SHARE', 'EVERYONE')
    orgs = config.get('FS_SHARE', 'ORG')
    groups = config.get('FS_SHARE', 'GROUPS')  # Groups are by ID. Multiple groups comma separated

    # --------------------------------------------------- get ArcGIS Server Proxy Info from .ini file
    use_prxy = False
    #use_prxy = config.get('PROXY', 'USEPROXY')
    pxy_srvr = config.get('PROXY', 'SERVER')
    pxy_port = config.get('PROXY', 'PORT')
    pxy_user = config.get('PROXY', 'USER')
    pxy_pass = config.get('PROXY', 'PASS')

    proxyDict = {}

    # If publishing to ArcGIS Server
    if ast.literal_eval(use_prxy):
        http_proxy = "http://" + pxy_user + ":" + pxy_pass + "@" + pxy_srvr + ":" + pxy_port
        https_proxy = "http://" + pxy_user + ":" + pxy_pass + "@" + pxy_srvr + ":" + pxy_port
        ftp_proxy = "http://" + pxy_user + ":" + pxy_pass + "@" + pxy_srvr + ":" + pxy_port
        proxyDict = {"http": http_proxy, "https": https_proxy, "ftp": ftp_proxy}

    # create a temp directory under the script
    tempDir = os.path.join(localPath, "tempDir")
    if not os.path.isdir(tempDir):
        os.mkdir(tempDir)
    finalSD = os.path.join(tempDir, serviceName + ".sd")

    # initialize AGOLHandler class
    agol = AGOLHandler(inputUsername, inputPswd, serviceName, folderName, proxyDict)

    # Turn map document into .SD file for uploading
    makeSD(MXD, serviceName, tempDir, finalSD, maxRecords, tags, summary)

    # overwrite the existing .SD on arcgis.com
    if agol.upload(finalSD, tags, summary):

        # publish the sd which was just uploaded
        fsID = agol.publish()

        # share the item
        if ast.literal_eval(shared):
            agol.enableSharing(fsID, everyone, orgs, groups)

        print("\nfinished.")

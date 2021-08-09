"""
Shared utils for dealing with XML.
"""

import glob
import re
import os.path
from xml.etree import ElementTree

def get_xml_element(xml_file, element_name):
    """ Gets a given element from a given xml file.

    Raises
    ------
    ValueError
        If the given xml_file does not exist.
        If the given xml_file does not contain an element with the given element_name.

    Returns
    -------
    xml.etree.ElementTree.Element
        The Element matching the given element_name.
    """

    # verify runtime config
    if not os.path.exists(xml_file):
        raise ValueError('Given xml file does not exist: ' + xml_file)

    # parse the xml file and figure out the namespace if there is one
    xml_xml = ElementTree.parse(xml_file)
    xml_root = xml_xml.getroot()
    xml_namespace_match = re.match(r'\{.*}', str(xml_root.tag))
    xml_namespace = ''
    if xml_namespace_match:
        xml_namespace = xml_namespace_match.group(0)

    # extract needed information from the xml file
    if xml_root.tag == element_name:
        xml_element = xml_root
    else:
        xml_element = xml_root.find('./' + xml_namespace + element_name)

    # verify information from xml file
    if xml_element is None:
        raise ValueError('Given xml file (' + \
             xml_file + \
             ') does not have ./' + \
             element_name + \
             ' element' \
        )

    return xml_element

def get_xml_element_by_path(
    xml_file_path,
    xpath,
    default_namespace=None,
    xml_namespace_dict=None,
    find_all=False
):
    """Gets the XML element(s) from a given xml file given an xpath.

    Parameters
    ----------
    xml_file_path : str
        Path of the xml file
    xpath : str
        Xpath of the element you want
    default_namespace : str
        Optional string specifying the default namespace you are using in your xpath selector.
        This is the most common argument that will most likely be used.
        If your XML is namespaced, then even if your elements are in the default namespace,
        you must specify and use this namespace in both your xpath as well as specifying it here.
    xml_namespace_dict : Dict[str, str]
        Optional dictionary if default_namespace is not enough and you have multiple
        namespaces that you need to deal with in your xpath selector.
    find_all : bool
        If False find only the first matching Element.
        If True find all matching elements.

    Returns
    -------
    xml.etree.ElementTree.Element or [xml.etree.ElementTree.Element]
        The Element(s) found given the xpath
    """
    # verify runtime config
    if not os.path.exists(xml_file_path):
        raise ValueError(f'Given xml file does not exist: {xml_file_path}')

    # figure out the xml namespaceing
    xml_file = ElementTree.parse(xml_file_path).getroot()
    namespaces = xml_namespace_dict
    if xml_namespace_dict is None and default_namespace is not None:
        xml_namespace_match = re.findall(r'{(.*?)}', xml_file.tag)
        xml_namespace = xml_namespace_match[0] if xml_namespace_match else ''
        namespaces = {}
        namespaces[default_namespace] = xml_namespace

    # find the element(s)
    results = None
    if find_all:
        results = xml_file.findall(xpath, namespaces)
    else:
        results = xml_file.find(xpath, namespaces)

    return results

def get_xml_element_text_by_path(
    xml_file_path,
    xpath,
    default_namespace=None,
    xml_namespace_dict=None,
    find_all=False
):
    """Gets the text of XML element(s) from a given xml file given an xpath.

    Parameters
    ----------
    xml_file_path : str
        Path of the xml file
    xpath : str
        Xpath of the element you want
    default_namespace : str
        Optional string specifying the default namespace you are using in your xpath selector.
        This is the most common argument that will most likely be used.
        If your XML is namespaced, then even if your elements are in the default namespace,
        you must specify and use this namespace in both your xpath as well as specifying it here.
    xml_namespace_dict : Dict[str, str]
        Optional dictionary if default_namespace is not enough and you have multiple
        namespaces that you need to deal with in your xpath selector.
    find_all : bool
        If False find only the first matching Element.
        If True find all matching elements.

    Returns
    -------
    str or [str]
        The text of the XML elements found given the xpath
    """
    xml_elements = get_xml_element_by_path(
        xml_file_path=xml_file_path,
        xpath=xpath,
        default_namespace=default_namespace,
        xml_namespace_dict=xml_namespace_dict,
        find_all=find_all
    )

    result = None
    if find_all:
        result = []
        for xml_element in xml_elements:
            result.append(xml_element.text)
    else:
        result = xml_elements.text

    return result

def aggregate_xml_element_attribute_values(xml_file_paths, xml_element, attribs): # pylint: disable=too-many-branches
    """Function to parse a XML file looking for a specific element and obtaining its attributes.

    If element is not found in file the file is ignored.

    If attribute is not found in element then any other attributes that are in the file are still
    aggregated.

    Parameters
    ----------
    xml_file_paths : str, [str]
        Path(s) to XML file(s) or directory(s) containing XML file(s)
    xml_element: str
        XML element being searched for
    attribs: list
        List of attributes being searched for in the XML element

    Returns
    --------
    report_results: dict
        A dictionary of attribute values.
    """
    report_results = {}

    if not isinstance(xml_file_paths, list):
        xml_file_paths = [xml_file_paths]

    # collect all the xml file paths
    xml_files = []
    for xml_file_path in xml_file_paths:
        if os.path.isdir(xml_file_path):
            xml_files += glob.glob(xml_file_path + '/*.xml', recursive=False)
        elif os.path.isfile(xml_file_path):
            xml_files += [xml_file_path]

    #Iterate over XML files
    for file in xml_files:
        try:
            #Add attributes to dictionary
            element = get_xml_element(file, xml_element)
            for attrib in attribs:
                if attrib in element.attrib:
                    # aggregate attribute accross multiple files
                    attribute_value = element.attrib[attrib]

                    if not attrib in report_results:
                        report_results[attrib] = []
                    report_results[attrib].append(attribute_value)
                else:
                    # ignore if a file has the element but missing an attribute
                    print(
                        f"WARNING: Did not find attribute ({attrib}) on element ({element})" \
                        f" in file ({file}). Ignoring."
                    )
                    continue
        except ValueError:
            # ignore if a file has the element but missing an attribute
            print(
                f"WARNING: Did not find element ({xml_element})" \
                f" in file ({file}). Ignoring."
            )
            continue

    #Loop to check if all values aggregated are integers, floats, strings, or a mix
    #of all three.
    for attrib in attribs:
        only_numerics = False
        only_floats = False

        #Iteration to determine what pattern all values follow.
        if attrib in report_results:
            for value in report_results[attrib]:
                #isnumeric() returns True if the value contains numbers
                #but not a decimal point. If this returns
                #true then continue because the value would be
                #a valid float anyway
                if value.isnumeric():
                    only_numerics = True
                    only_floats = True
                else:
                    only_numerics = False
                    try:
                        float(value)
                        only_floats = True
                    except ValueError:
                        only_floats = False
                        #Break since only_numerics and only_floats are both false
                        break

            if only_numerics or only_floats:
                aggregated_value = 0
            else:
                aggregated_value = []

            #Iteration to aggregate values based on determined pattern.
            for value in report_results[attrib]:
                #If a value is numeric and can be a float then it is an integer
                if only_numerics:
                    aggregated_value = int(aggregated_value) + int(value)
                #If a value is not numeric but can be a float then it is a float
                elif only_floats:
                    aggregated_value = float(aggregated_value) + float(value)
                else:
                    aggregated_value.append(value)
        else:
            aggregated_value = None

        #Replace list of values with aggregated value that is either an int,
        #float, or string
        if aggregated_value is not None:
            report_results[attrib] = aggregated_value

    return report_results

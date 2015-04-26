"""
Generate address space c++ code from xml file specification
"""
import sys

import xml.etree.ElementTree as ET

class ObjectStruct(object):
    def __init__(self):
        self.nodetype = None
        self.nodeid = None
        self.browsename = None 
        self.displayname = None
        self.symname = None
        self.parent = None
        self.parentlink = None
        self.desc = ""
        self.typedef = None
        self.refs = []
        self.nodeclass = None
        self.eventnotifier = 0 

        #variable
        self.datatype = None
        self.rank = -1 # checl default value
        self.value = []
        self.valuetype = None
        self.dimensions = None
        self.accesslevel = None 
        self.useraccesslevel = None
        self.minsample = None

        #referencetype
        self.inversename = ""
        self.abstract = "false"
        self.symmetric = "false"

        #datatype
        self.definition = []

        #types


class RefStruct():
    def __init__(self):
        self.reftype = None
        self.forward = "true"
        self.target = None


class CodeGenerator(object):
    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
        self.output_file = None
        self.part = self.input_path.split(".")[-2]
        self.aliases = {}

    def run(self):
        sys.stderr.write("Generating Python code {} for XML file {}".format(self.output_path, self.input_path) + "\n")
        self.output_file = open(self.output_path, "w")
        self.make_header()
        tree = ET.parse(xmlpath)
        root = tree.getroot()
        for child in root:
            if child.tag[51:] == 'UAObject':
                node = self.parse_node(child)
                self.make_object_code(node)
            elif child.tag[51:] == 'UAObjectType':
                node = self.parse_node(child)
                self.make_object_type_code(node)
            elif child.tag[51:] == 'UAVariable':
                node = self.parse_node(child)
                self.make_variable_code(node)
            elif child.tag[51:] == 'UAVariableType':
                node = self.parse_node(child)
                self.make_variable_type_code(node)
            elif child.tag[51:] == 'UAReferenceType':
                node = self.parse_node(child)
                self.make_reference_code(node)
            elif child.tag[51:] == 'UADataType':
                node = self.parse_node(child)
                self.make_datatype_code(node)
            elif child.tag[51:] == 'UAMethod':
                node = self.parse_node(child)
                self.make_method_code(node)
            elif child.tag[51:] == 'Aliases':
                for el in child:
                    self.aliases[el.attrib["Alias"]] = el.text
            else:
                sys.stderr.write("Not implemented node type: " + child.tag[51:] + "\n")

    def writecode(self, *args):
        self.output_file.write(" ".join(args) + "\n")

    def make_header(self, ):
        self.writecode('''
"""
DO NOT EDIT THIS FILE!
It is automatically generated from opcfoundation.org schemas.
"""

from opcua import uaprotocol as ua

false = False #FIXME
true = True #FIXME

def create_standard_address_space_%s(server):
  ''' % (self.part))


    def parse_node(self, child):
        obj = ObjectStruct()
        obj.nodetype = child.tag[53:]
        for key, val in child.attrib.items():
            if key == "NodeId":
                obj.nodeid = val
            elif key == "BrowseName":
                obj.browsename = val
            elif key == "SymbolicName":
                obj.symname = val
            elif key == "ParentNodeId":
                obj.parent = val
            elif key == "DataType":
                obj.datatype = val
            elif key == "IsAbstract":
                obj.abstract = val
            elif key == "EventNotifier":
                obj.eventnotifier = val
            elif key == "ValueRank":
                obj.rank = val
            elif key == "ArrayDimensions":
                obj.dimensions = val
            elif key == "MinimumSamplingInterval":
                obj.minsample = val
            elif key == "AccessLevel":
                obj.accesslevel = val
            elif key == "UserAccessLevel":
                obj.useraccesslevel = val
            elif key == "Symmetric":
                obj.symmetric = val
            else:
                sys.stderr.write("Attribute not implemented: " + key + " " + val + "\n")

        obj.displayname = obj.browsename#FIXME
        for el in child:
            tag = el.tag[51:]

            if tag == "DisplayName":
                obj.displayname = el.text
            elif tag == "Description":
                obj.desc = el.text
            elif tag == "References":
                for ref in el:
                    #self.writecode("ref", ref, "IsForward" in ref, ref.text )
                    if ref.attrib["ReferenceType"] == "HasTypeDefinition":
                        obj.typedef = ref.text
                    elif "IsForward" in ref.attrib and ref.attrib["IsForward"] == "false":
                        #if obj.parent:
                            #sys.stderr.write("Parent is already set with: "+ obj.parent + " " + ref.text + "\n") 
                        obj.parent = ref.text
                        obj.parentlink = ref.attrib["ReferenceType"]
                    else:
                        struct = RefStruct()
                        if "IsForward" in ref.attrib: struct.forward = ref.attrib["IsForward"]
                        struct.target = ref.text
                        struct.reftype = ref.attrib["ReferenceType"] 
                        obj.refs.append(struct)
            elif tag == "Value":
                for val in el:
                    ntag = val.tag[47:]
                    obj.valuetype = ntag
                    if ntag == "Int32":
                        obj.value.append(val.text)
                    elif ntag == "UInt32":
                        obj.value.append(val.text)
                    elif ntag in ('ByteString', 'String'):
                        mytext = val.text.replace('\n', '').replace('\r', '')
                        obj.value.append('b"{}"'.format(mytext))
                    elif ntag == "ListOfExtensionObject":
                        pass
                    elif ntag == "ListOfLocalizedText":
                        pass
                    else:
                        self.writecode("Missing type: ", ntag)
            elif tag == "InverseName":
                obj.inversename = el.text
            elif tag == "Definition":
                for field in el:
                    obj.definition.append(field)
            else:
                sys.stderr.write("Not implemented tag: "+ str(el) + "\n")
        return obj

    def make_node_code(self, obj, indent):
        self.writecode(indent, 'node = ua.AddNodesItem()')
        self.writecode(indent, 'node.RequestedNewNodeId = ua.NodeId.from_string("{}")'.format(obj.nodeid))
        self.writecode(indent, 'node.BrowseName = ua.QualifiedName.from_string("{}")'.format(obj.browsename))
        self.writecode(indent, 'node.NodeClass = ua.NodeClass.{}'.format(obj.nodetype))
        if obj.parent: self.writecode(indent, 'node.ParentNodeId = ua.NodeId.from_string("{}")'.format(obj.parent))
        if obj.parent: self.writecode(indent, 'node.ReferenceTypeId = {}'.format(self.to_ref_type(obj.parentlink)))
        if obj.typedef: self.writecode(indent, 'node.TypeDefinition = ua.NodeId.from_string("{}")'.format(obj.typedef))

    def to_vector(self, dims):
        s = "["
        s += dims
        s+= "]"
        return s

    def to_data_type(self, nodeid):
        if not nodeid:
            return "ua.NodeId(ua.ObjectIds.String)"
        if "=" in nodeid:
            return 'ua.NodeId.from_string("{}")'.format(nodeid)
        else:
            return 'ua.NodeId(ua.ObjectIds.{})'.format(nodeid)

    def to_ref_type(self, nodeid):
        if not "=" in nodeid:
            nodeid = self.aliases[nodeid]
        return 'ua.NodeId.from_string("{}")'.format(nodeid)

    def make_object_code(self, obj):
        indent = "   "
        self.writecode(indent)
        self.make_node_code(obj, indent)
        self.writecode(indent, 'attrs = ua.ObjectAttributes()')
        if obj.desc: self.writecode(indent, 'attrs.Description = ua.LocalizedText("{}")'.format(obj.desc))
        self.writecode(indent, 'attrs.DisplayName = ua.LocalizedText("{}")'.format(obj.displayname))
        self.writecode(indent, 'attrs.EventNotifier = {}'.format(obj.eventnotifier))
        self.writecode(indent, 'node.NodeAttributes = attrs')
        self.writecode(indent, 'server.add_nodes([node])')
        self.make_refs_code(obj, indent)

    def make_object_type_code(self, obj):
        indent = "   "
        self.writecode(indent)
        self.make_node_code(obj, indent)
        self.writecode(indent, 'attrs = ua.ObjectTypeAttributes()')
        if obj.desc: self.writecode(indent, 'attrs.Description = ua.LocalizedText("{}")'.format(obj.desc))
        self.writecode(indent, 'attrs.DisplayName = ua.LocalizedText("{}")'.format(obj.displayname))
        self.writecode(indent, 'attrs.IsAbstract = {}'.format(obj.abstract))
        self.writecode(indent, 'node.NodeAttributes = attrs')
        self.writecode(indent, 'server.add_nodes([node])')
        self.make_refs_code(obj, indent)


    def make_variable_code(self, obj):
        indent = "   "
        self.writecode(indent)
        self.make_node_code(obj, indent)
        self.writecode(indent, 'attrs = ua.VariableAttributes()')
        if obj.desc: self.writecode(indent, 'attrs.Description = ua.LocalizedText("{}")'.format(obj.desc))
        self.writecode(indent, 'attrs.DisplayName = ua.LocalizedText("{}")'.format(obj.displayname))
        self.writecode(indent, 'attrs.DataType = {}'.format(self.to_data_type(obj.datatype)))
        if obj.value and len(obj.value) == 1: self.writecode(indent, 'attrs.Value = ua.Variant({}, ua.VariantType.{})'.format(obj.value[0],obj.valuetype ))
        if obj.rank: self.writecode(indent, 'attrs.ValueRank = {}'.format(obj.rank))
        if obj.accesslevel: self.writecode(indent, 'attrs.AccessLevel = {}'.format(obj.accesslevel))
        if obj.useraccesslevel: self.writecode(indent, 'attrs.UserAccessLevel = {}'.format(obj.useraccesslevel))
        if obj.minsample: self.writecode(indent, 'attrs.MinimumSamplingInterval = {}'.format(obj.minsample))
        if obj.dimensions: self.writecode(indent, 'attrs.ArrayDimensions = {}'.format(self.to_vector(obj.dimensions)))
        self.writecode(indent, 'node.NodeAttributes = attrs')
        self.writecode(indent, 'server.add_nodes([node])')
        self.make_refs_code(obj, indent)

    def make_variable_type_code(self, obj):
        indent = "   "
        self.writecode(indent)
        self.make_node_code(obj, indent)
        self.writecode(indent, 'attrs = ua.VariableTypeAttributes()')
        if obj.desc: self.writecode(indent, 'attrs.Description = ua.LocalizedText("{}")'.format(obj.desc))
        self.writecode(indent, 'attrs.DisplayName = ua.LocalizedText("{}")'.format(obj.displayname))
        self.writecode(indent, 'attrs.DataType = {}'.format(self.to_data_type(obj.datatype)))
        if obj.value and len(obj.value) == 1: self.writecode(indent, 'attrs.Value = {}'.format(obj.value[0]))
        if obj.rank: self.writecode(indent, 'attrs.ValueRank = {}'.format(obj.rank))
        if obj.abstract: self.writecode(indent, 'attrs.IsAbstract = {}'.format(obj.abstract))
        if obj.dimensions: self.writecode(indent, 'attrs.ArrayDimensions = {}'.format(self.to_vector(obj.dimensions)))
        self.writecode(indent, 'node.NodeAttributes = attrs')
        self.writecode(indent, 'server.add_nodes([node])')
        self.make_refs_code(obj, indent)


    def make_method_code(self, obj):
        indent = "   "
        self.writecode(indent)
        self.make_node_code(obj, indent)
        self.writecode(indent, 'attrs = ua.MethodAttributes()')
        if obj.desc: self.writecode(indent, 'attrs.Description = ua.LocalizedText("{}")'.format(obj.desc))
        self.writecode(indent, 'attrs.DisplayName = ua.LocalizedText("{}")'.format(obj.displayname))
        if obj.accesslevel: self.writecode(indent, 'attrs.AccessLevel = {}'.format(obj.accesslevel))
        if obj.useraccesslevel: self.writecode(indent, 'attrs.UserAccessLevel = {}'.format(obj.useraccesslevel))
        if obj.minsample: self.writecode(indent, 'attrs.MinimumSamplingInterval = {}'.format(obj.minsample))
        if obj.dimensions: self.writecode(indent, 'attrs.ArrayDimensions = {}'.format(self.to_vector(obj.dimensions)))
        self.writecode(indent, 'node.NodeAttributes = attrs')
        self.writecode(indent, 'server.add_nodes([node])')
        self.make_refs_code(obj, indent)



    def make_reference_code(self, obj):
        indent = "   "
        self.writecode(indent)
        self.make_node_code(obj, indent)
        self.writecode(indent, 'attrs = ua.ReferenceTypeAttributes()')
        if obj.desc: self.writecode(indent, 'attrs.Description = ua.LocalizedText("{}")'.format(obj.desc))
        self.writecode(indent, 'attrs.DisplayName = ua.LocalizedText("{}")'.format(obj.displayname))
        if obj. inversename: self.writecode(indent, 'attrs.InverseName = ua.LocalizedText("{}")'.format(obj.inversename))
        if obj.abstract: self.writecode(indent, 'attrs.IsAbstract = {}'.format(obj.abstract))
        if obj.symmetric: self.writecode(indent, 'attrs.Symmetric = {}'.format(obj.symmetric))
        self.writecode(indent, 'node.NodeAttributes = attrs')
        self.writecode(indent, 'server.add_nodes([node])')
        self.make_refs_code(obj, indent)

    def make_datatype_code(self, obj):
        indent = "   "
        self.writecode(indent)
        self.make_node_code(obj, indent)
        self.writecode(indent, 'attrs = ua.DataTypeAttributes()')
        if obj.desc: self.writecode(indent, u'attrs.Description = ua.LocalizedText("{}")'.format(obj.desc.encode('ascii', 'replace')))
        self.writecode(indent, 'attrs.DisplayName = ua.LocalizedText("{}")'.format(obj.displayname))
        if obj.abstract: self.writecode(indent, 'attrs.IsAbstract = {}'.format(obj.abstract))
        self.writecode(indent, 'node.NodeAttributes = attrs')
        self.writecode(indent, 'server.add_nodes([node])')
        self.make_refs_code(obj, indent)

    def make_refs_code(self, obj, indent):
        if not obj.refs:
            return
        self.writecode(indent, "refs = []")
        for ref in obj.refs:
            self.writecode(indent, 'ref = ua.AddReferencesItem()')
            self.writecode(indent, 'ref.IsForward = true')
            self.writecode(indent, 'ref.ReferenceTypeId = {}'.format(self.to_ref_type(ref.reftype)))
            self.writecode(indent, 'ref.SourceNodeId = ua.NodeId.from_string("{}")'.format(obj.nodeid))
            self.writecode(indent, 'ref.TargetNodeClass = ua.NodeClass.DataType')
            self.writecode(indent, 'ref.TargetNodeId = ua.NodeId.from_string("{}")'.format(ref.target))
            self.writecode(indent, "refs.append(ref)")
        self.writecode(indent, 'server.add_references(refs)')

def save_aspace_to_disk():
    import os.path
    path = os.path.join("..", "opcua", "binary_address_space.pickle")
    print("Savind standard address space to:", path)
    sys.path.append("..")
    from opcua import address_space
    from opcua import standard_address_space
    aspace = address_space.AddressSpace()
    standard_address_space.fill_address_space(aspace)
    aspace.dump(path)

if __name__ == "__main__":
    for i in (3, 4, 5, 8, 9, 10, 11, 13):
        xmlpath = "Opc.Ua.NodeSet2.Part{}.xml".format(str(i))
        cpppath = "../opcua/standard_address_space_part{}.py".format(str(i))
        c = CodeGenerator(xmlpath, cpppath)
        c.run()

    save_aspace_to_disk()



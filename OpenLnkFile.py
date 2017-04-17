import sublime, sublime_plugin
import os.path
import sys
import struct

def GetShortPath(path):
    target = ''

    try:
        with open(path, 'rb') as stream:
            content = stream.read()

            # skip first 20 bytes (HeaderSize and LinkCLSID)
            # read the LinkFlags structure (4 bytes)
            lflags = struct.unpack('I', content[0x14:0x18])[0]
            position = 0x18

            # if the HasLinkTargetIDList bit is set then skip the stored IDList
            # structure and header
            if (lflags & 0x01) == 1:
                position = struct.unpack('H', content[0x4C:0x4E])[0] + 0x4E

            last_pos = position
            position += 0x04

            # get how long the file information is (LinkInfoSize)
            length = struct.unpack('I', content[last_pos:position])[0]

            # skip 12 bytes (LinkInfoHeaderSize, LinkInfoFlags, and VolumeIDOffset)
            position += 0x0C

            # go to the LocalBasePath position
            lbpos = struct.unpack('I', content[position:position+0x04])[0]
            position = last_pos + lbpos

            # read the string at the given position of the determined length
            size= (length + last_pos) - position - 0x02
            temp = struct.unpack('c' * size, content[position:position+size])
            target = b''.join(temp).decode(sys.getfilesystemencoding())
    except:
        # could not read the file
        pass
    return target

class OpenLnkFile(sublime_plugin.EventListener):
    def on_load2(self, view):
        window = view.window()
        path = view.file_name()
        ext = os.path.splitext(path)[1]
        if ext==".lnk":
            window.focus_view(view)
            window.run_command('close_file')
            real_path = GetShortPath(path)
            if os.path.isdir(real_path):
                data = window.project_data()
                if not data:
                    data = {}
                if "folders" not in data:
                    data["folders"] = []
                if {'path': real_path} not in data["folders"]:
                    data["folders"].append({'path': real_path})
                    window.set_project_data(data)
            else:
                window.open_file(GetShortPath(path))

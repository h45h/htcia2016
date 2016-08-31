import pytsk3

SEP = '*********************************'
# With backslashes, escape by doubling
img = pytsk3.Img_Info("\\\\.\\C:")
fs_info = pytsk3.FS_Info(img)

# Absolute paths only, use forward slashes
things_to_open = ['/Users/monkey/PycharmProjects/htcia2016/ads.txt', '/Users/monkey/PycharmProjects/htcia2016']

for path in things_to_open:
    file_entry = fs_info.open(path)
    print SEP
    print path
    print SEP
    streams = 0
    # Get metadata on what the thing is:
    print "This file entry is a {0}.".format(file_entry.info.meta.type)
    for attr in file_entry:
        print "Found attribute type {0}.".format(attr.info.type)
        offset = 0
        size = attr.info.size
        print "Attr {0} is called {1}. The size is {2}.".format(attr.info.id, attr.info.name, size)

        # Since we're on Windows, we want NTFS_DATA streams
        if attr.info.type == pytsk3.TSK_FS_ATTR_TYPE_NTFS_DATA:
            while offset < size:
                available_to_read = min(1024*1024, size - offset)
                data = file_entry.read_random(offset, available_to_read, attr.info.type, attr.info.id)
                if not data:
                    break
                offset += len(data)
                # Do something with data

        # This is what you would see as $I30 in FTK.
        if attr.info.type == pytsk3.TSK_FS_ATTR_TYPE_NTFS_IDXALLOC:
            size = attr.info.size
            offset = 0
            while offset < size:
                available_to_read = min(1024*1024, size - offset)
                data = file_entry.read_random(offset, available_to_read, attr.info.type, attr.info.id)
                if not data:
                    break
                offset += len(data)
                # Do something with data

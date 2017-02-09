#!/usr/bin/env python2.7

"""
CanvasSync by Mathias Perslev

MSc Bioinformatics, University of Copenhagen
February 2017
"""

"""
module.py, Third level class in hierarchy

The Module class is the third level Entity object in the folder hierarchy. It inherits from the base Entity
class and extends its functionality to allow downloading information on Items listed under the module in the Canvas
system. An Item object or Folder object is initialized for each item found and appended to a list of children under the
Module object.
"""

# CanvasSync modules
from CanvasSync.CanvasEntities.entity import Entity
from CanvasSync.CanvasEntities.file import File
from CanvasSync.CanvasEntities.page import Page
from CanvasSync.CanvasEntities.external_url import ExternalUrl
from CanvasSync.Statics.ANSI import ANSI
from CanvasSync.Statics import static_functions


class Module(Entity):
    """ Derived class of the Entity base class """

    def __init__(self, module_info, module_position, parent):
        """
        Constructor method, initializes base Entity class and adds all children Folder and/or Item objects to the
        list of children

        module_info     : dict   | A dictionary of information on the Canvas module object
        module_position : int    | An integer representing the position of the module in the folder (1 for first folder)
        parent          : object | The parent object, a Course object
        """

        self.module_info = module_info

        module_id = self.module_info["id"]
        module_name = static_functions.get_corrected_name(self.module_info["name"])
        module_path = parent.get_path() + u"%s - %s" % (module_position, module_name)

        # Initialize base class
        Entity.__init__(self,
                        id_number=module_id,
                        name=module_name,
                        sync_path=module_path,
                        parent=parent)

    def __repr__(self):
        """ String representation, overwriting base class method """
        status = ANSI.format("[SYNCED]", formatting="green")
        return status + u" " * 7 + u"|   " + u"\t" * self.indent + u"%s: %s" \
                                                                   % (ANSI.format("Module", formatting="module"),
                                                                      self.name)

    def get_item_information(self):
        """ Returns a dictionary of items from the Canvas server """
        return self.api.get_items(self.get_parent().get_id(), self.id)

    def add_sub_folder(self, folder_info, folder_position, folder_items):
        """
        [HIDDEN] Method that adds a Folder object to the list of children

        folder_id       : int    | The ID number of the folder to initialize an Folder object on
        folder_name     : string | The name representation of the folder
        folder_position : int    | An integer representing the position of the folder in the parent folder, such that
                                   the folder listed first in Canvas gets the folder_position '1'.
        folder_items    : dict   | A dictionary of information on items contained by the sub-folder
        """

        # Initialize Folder object and add to list of children, then sync
        from CanvasSync.CanvasEntities.subfolder import SubFolder

        sub_folder = SubFolder(folder_info, folder_position, parent=self, items=folder_items)
        self.add_child(sub_folder)

    def add_file(self, file_information):
        """
        Method that adds an Item object to the list of children and synchronizes it
        """

        detailed_file_info = self.api.download_item_information(file_information["url"])

        # Initialize Item object and add to list of children
        item = File(detailed_file_info, self)
        self.add_child(item)

    def add_page(self, page_information):
        """
        Method that adds a Page object to the list of children and synchronizes it
        """

        # Initialize Page object and add to list of children
        page = Page(page_information, self)
        self.add_child(page)

    def add_url(self, url_information):
        """
        Method that adds an ExternalUrl object to the list of children and synchronizes it
        """

        # Initialize ExternalUrl object and add to list of children
        url = ExternalUrl(url_information, self)
        self.add_child(url)

    def add_items(self, items=None):
        """
        Method that adds all Items under the module to the list of children.
        If the item is a sub-folder it will be added as a Folder object instead.

        items : list | A list of dictionaries of information on items
                       SubFolders inherit from the Module class and use this feature
        """

        # If the Folder was initialized with an items dictionary, skip downloading
        if not items:
            items = self.get_item_information()

        # Determine which items are in the outer-scope (located in the folder represented by this module) and which
        # items are located in sub-folders under this module.
        items_in_this_scope, sub_folders = static_functions.reorganize(items)

        # Add all non-sub-folder items to the list of children. Currently, files, HTML pages and URLs are added.
        for item in items_in_this_scope:
            if item["type"] == "File":
                self.add_file(item)
            elif item["type"] == "Page":
                self.add_page(item)
            elif item["type"] == "ExternalUrl":
                self.add_url(item)

        # Add all sub-folders as Folder objects to the list of children along with the items the folder contain
        for position, folder in enumerate(sub_folders):
            self.add_sub_folder(folder[0], position + 1, folder[1:])

    def get_folders(self):
        """ Getter-method for the list of children, calls _get_children method of base class """
        return self.get_children()

    def walk(self, counter):
        """
        Walk by adding all File, Page, ExternalLink and SubFolder objects to the list of children
        Overwritten in derived SubFolder class
        """
        self.add_items()

        counter[0] += 1
        print unicode(self)
        for item in self:
            item.walk(counter)

    def sync(self):
        """
        1) Adding all File, Page, ExternalLink and SubFolder objects to the list of children
        2) Synchronize all children objects
        """
        print unicode(self)

        self.add_items()

        for item in self:
            item.sync()

    def show(self):
        """ Show the folder hierarchy by printing every level """
        print unicode(self)

        for item in self:
            item.show()

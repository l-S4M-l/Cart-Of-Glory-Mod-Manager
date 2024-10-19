from PyQt5 import QtCore, QtGui, QtWidgets
from QtTitleBarManager import title_bar_handler
from mainui import Ui_Form as mainui_form
import os
import sys
import zipfile
import json
import shutil
import stat

class mainui(mainui_form,QtWidgets.QWidget):
    def setupUi(self, Form):
        super().setupUi(Form)
        self.cwd = os.getcwd().replace("\\","/")
        self.refresh_mod_list()

        title_bar_handler(Form,self.titlebar,self.close_but,self.mini_but)

        self.logo.setPixmap(QtGui.QPixmap(f"{self.cwd}/assets/icon.png"))
        self.logo.setStyleSheet("background-color:rgba(0,0,0,0);")

        self.icon.setPixmap(QtGui.QPixmap(f"{self.cwd}/assets/icon.png"))

        self.rightbg_image.setPixmap(QtGui.QPixmap(f"{self.cwd}/assets/arrow right.png"))
        self.right_but.setStyleSheet("background-color:rgba(0,0,0,0);")
        self.leftbg_image.setPixmap(QtGui.QPixmap(f"{self.cwd}/assets/arrow left.png"))
        self.left_but.setStyleSheet("background-color:rgba(0,0,0,0);")

        self.add_mod_but.setStyleSheet("background-color:rgba(0,0,0,0);")
        self.add_mod_image.setPixmap(QtGui.QPixmap(f"{self.cwd}/assets/add_mod.png"))

        self.setting_cog.setStyleSheet(f"""background-color:rgba(0,0,0,0);background-image:url({self.cwd}/assets/cog.png);background-size: contain;""")

        with open(f"{self.cwd}/Settings.json","r+") as file:
            settings = json.loads(file.read())
            file.close()

        self.game_path.setText(settings["user setting"]["gamepath"])

        self.events()
    
    def events(self):
        self.add_mod_but.clicked.connect(self.add_mods)
        self.left_but.clicked.connect(self.add_to_active_mods)
        self.right_but.clicked.connect(self.remove_mod)
        self.setting_cog.clicked.connect(lambda : self.settings_bg.setGeometry(QtCore.QRect(0, 20, 1104, 537)))
        self.back_settings.clicked.connect(lambda : self.settings_bg.setGeometry(QtCore.QRect(10000, 20, 1104, 537)))
        self.browse_game_path.clicked.connect(self.game_path_clicked)
        self.motion_blur.clicked.connect(self.remove_motion_blur)

    def game_path_clicked(self):
        file_path = QtWidgets.QFileDialog.getExistingDirectory(caption="Open Game Folder")

        with open(f"{self.cwd}/Settings.json","r+") as file:
            settings = json.loads(file.read())
            file.close()
        
        settings["user setting"]["gamepath"] = file_path
        self.game_path.setText(file_path)

        with open(f"{self.cwd}/Settings.json","w+") as file:
            file.write(json.dumps(settings,indent=4))

    def remove_motion_blur(self):
        local_path = os.path.expandvars(r"%localappdata%").replace("\\","/")
        engine_file = f"{local_path}/CartOfGlory/Saved/Config/WindowsNoEditor/Engine.ini"

        file_permissions = os.stat(engine_file).st_mode
        os.chmod(engine_file, file_permissions | stat.S_IWUSR)

        with open(engine_file,"r+") as file:
            file_data = file.read()
        
        if file_data.find("r.MotionBlur.Max=0") == -1:
            file_data = f"""{file_data}

[SystemSettings]
r.MotionBlur.Max=0
r.MotionBlurQuality=0
r.LightShafts=0
r.LightShaftQuality=0
r.GenerateMeshDistanceFields=False"""

            with open(engine_file,"w+") as file:
                file.write(file_data)

            os.chmod(engine_file, file_permissions & ~stat.S_IWUSR)
        
    def add_mods(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(caption="Open Mod",filter="ZIP Files (*.zip)")

        if os.path.isfile(file_path) != True:
            return
        
        if os.path.isdir(f"{self.cwd}/mods") != True:
            os.mkdir(f"{self.cwd}/mods")
        
        zip_name = os.path.splitext(os.path.basename(file_path))[0]

        with zipfile.ZipFile(file_path,"r") as zip_ref:
            zip_ref.extractall(f"{self.cwd}/mods/{zip_name}")

        with open(f"{self.cwd}/mods/{zip_name}/info.json","r+") as file:
            mod_data = json.loads(file.read())
            file.close()

        if mod_data == None:
            return
        
        with open(f"{self.cwd}/Settings.json","r+") as file:
            settings = json.loads(file.read())
            file.close()
        
        if settings == None:
            settings = {"user setting":{},"active mods":[],"mods":[]}
        
        settings["mods"].append(mod_data)

        with open(f"{self.cwd}/Settings.json","w+") as file:
            file.write(json.dumps(settings,indent=4))

        self.refresh_mod_list()

    def refresh_mod_list(self):
        with open(f"{self.cwd}/Settings.json","r+") as file:
            settings = json.loads(file.read())
            file.close()
        
        self.inactive_mods.clear()
        self.active_mods.clear()

        mod_list = []
        for i in settings["mods"]:

            mod_list.append(f'{i["name"]} - {i["version"]}: replaces {i["external"]}')

        self.inactive_mods.addItems(mod_list)

        mod_list = []
        for i in settings["active mods"]:

            mod_list.append(f'{i["name"]} - {i["version"]}: replaces {i["external"]}')

        self.active_mods.addItems(mod_list)

    def add_to_active_mods(self):
        with open(f"{self.cwd}/Settings.json","r+") as file:
            settings = json.loads(file.read())
            file.close()
        
        try:
            current_item:QtWidgets.QListWidgetItem = self.inactive_mods.selectedItems()[0]
        except:
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle("Popup")
            msg.setText("Please Select a mod to move")
            msg.exec_()
            return


        for i in settings["mods"]:
            if i["name"] == current_item.text().split(" - ")[0]:
                selected_mod = i
            

        for val, i in enumerate(settings["active mods"]):
            if selected_mod["replaces"] == i["replaces"]:
                self.delete_mod(i)
                del settings["active mods"][val]
            
            elif selected_mod["name"] == i["name"]:
                del settings["active mods"][val]
                

        shutil.copytree(f"{self.cwd}/mods/{selected_mod["name"]}/CartOfGlory", f'{settings["user setting"]["gamepath"]}/CartOfGlory',dirs_exist_ok=True)
        settings["active mods"].append(selected_mod)

        with open(f"{self.cwd}/Settings.json","w+") as file:
            file.write(json.dumps(settings,indent=4))

        self.refresh_mod_list()

    def delete_mod(self,mod_info):
        with open(f"{self.cwd}/Settings.json","r+") as file:
            settings = json.loads(file.read())
            file.close()

        if mod_info["type"] == 1: #maps
            self.clear_second_path(
                f"{self.cwd}/mods/{mod_info["name"]}/CartOfGlory/Content/Levels",
                f"{settings["user setting"]["gamepath"]}/CartOfGlory/Content/Levels")
        
        if mod_info["type"] == 2: #carts
            self.clear_second_path(
                f"{self.cwd}/mods/{mod_info["name"]}/CartOfGlory/Content/Art/Carts",
                f"{settings["user setting"]["gamepath"]}/CartOfGlory/Content/Art/Carts")
            
        if mod_info["type"] == 3: #characters
            self.clear_second_path(
                f"{self.cwd}/mods/{mod_info["name"]}/CartOfGlory/Content/Art/Characters_New",
                f"{settings["user setting"]["gamepath"]}/CartOfGlory/Content/Art/Characters_New")
            
    def remove_mod(self):
        with open(f"{self.cwd}/Settings.json","r+") as file:
            settings = json.loads(file.read())
            file.close()
        
        try:
            current_item:QtWidgets.QListWidgetItem = self.active_mods.selectedItems()[0]
        except:
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle("Popup")
            msg.setText("Please Select a active mod to move")
            msg.exec_()
            return


        for i in settings["mods"]:
            if i["name"] == current_item.text().split(" - ")[0]:
                selected_mod = i
            
        if selected_mod != None:
            self.delete_mod(selected_mod)

        for val, i in enumerate(settings["active mods"]):
            if i == selected_mod:
                del settings["active mods"][val]

        with open(f"{self.cwd}/Settings.json","w+") as file:
            file.write(json.dumps(settings,indent=4))

        self.refresh_mod_list()



    #tools
    def clear_second_path(self, path1, path2):
        # Ensure the paths are valid directories
        if not os.path.isdir(path1):
            raise ValueError(f"The first path '{path1}' is not a valid directory.")
        if not os.path.isdir(path2):
            raise ValueError(f"The second path '{path2}' is not a valid directory.")
        
        # Get all files and folders in the first path
        items_to_copy = os.listdir(path1)

        # Remove all files and folders from the second path
        for item in items_to_copy:
            item_path = os.path.join(path2, item)
            if os.path.exists(item_path):
                if os.path.isfile(item_path):
                    os.remove(item_path)  # Remove file
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)  # Remove directory




        
        
        


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = mainui()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())
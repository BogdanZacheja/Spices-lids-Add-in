import adsk.core, traceback
import os
from ...lib import fusionAddInUtils as futil
from ... import config
app = adsk.core.Application.get()
ui = app.userInterface


# TODO *** Specify the command identity information. ***
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdDialog'
CMD_NAME = 'Command Dialog Sample'
CMD_Description = 'A Fusion Add-in Command with a dialog'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the 
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []

def start():
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
    futil.add_handler(cmd_def.commandCreated, command_created)
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    control = panel.controls.itemById(CMD_ID)
    if not control:
        control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
        control.isPromoted = IS_PROMOTED

def stop():
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    if command_control:
        command_control.deleteMe()
    if command_definition:
        command_definition.deleteMe()

def command_created(args: adsk.core.CommandCreatedEventArgs):
    inputs = args.command.commandInputs

    # Input for Input File Path
    input_file_path = inputs.addTextBoxCommandInput('input_file_path', 'Select CSV file', '', 1, True)
    input_file_button = inputs.addBoolValueInput('input_file_icon', 'Select', False, os.path.join(ICON_FOLDER, '16x16.png'), True)
    
    # Input for Output Folder Path
    output_folder_path = inputs.addTextBoxCommandInput('output_folder_path', 'Select Output Folder', '', 1, True)
    output_folder_button = inputs.addBoolValueInput('output_folder_icon', 'Select', False, os.path.join(ICON_FOLDER, '16x16.png'), True)

    # Sliders
    inputs.addFloatSliderCommandInput('jar_lid_diameter', 'Jar Lid Diameter (mm)', 'mm', 0, 100, False).valueOne = 50
    inputs.addFloatSliderCommandInput('text_size', 'Text Size (mm)', 'mm', 0, 20, False).valueOne = 5
    inputs.addFloatSliderCommandInput('text_height', 'Text Height (mm)', 'mm', 0, 10, False).valueOne = 2

    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)

def command_input_changed(args: adsk.core.InputChangedEventArgs):
    inputs = args.inputs
    if args.input.id == 'input_file_icon':
        file_dialog = ui.createFileDialog()
        file_dialog.isMultiSelectEnabled = False
        file_dialog.title = 'Select Input CSV File'
        file_dialog.filter = 'CSV files (*.csv)'
        file_dialog.filterIndex = 0
        dialog_result = file_dialog.showOpen()
        if dialog_result == adsk.core.DialogResults.DialogOK:
            inputs.itemById('input_file_path').text = file_dialog.filename

    elif args.input.id == 'output_folder_icon':
        folder_dialog = ui.createFolderDialog()
        folder_dialog.title = 'Select Output Folder'
        dialog_result = folder_dialog.showDialog()
        if dialog_result == adsk.core.DialogResults.DialogOK:
            inputs.itemById('output_folder_path').text = folder_dialog.folder

def command_execute(args: adsk.core.CommandEventArgs):
    inputs = args.command.commandInputs
    input_file_path = inputs.itemById('input_file_path').text
    output_folder_path = inputs.itemById('output_folder_path').text
    jar_lid_diameter = inputs.itemById('jar_lid_diameter').valueOne
    text_size = inputs.itemById('text_size').valueOne
    text_height = inputs.itemById('text_height').valueOne

    ui.messageBox(f'Input File: {input_file_path}\nOutput Folder: {output_folder_path}\nJar Lid Diameter: {jar_lid_diameter}\nText Size: {text_size}\nText Height: {text_height}')

    try:
        design = app.activeProduct
        rootComp = design.rootComponent
        sk = rootComp.sketches.itemByName('ChangeText')
        skText = sk.sketchTexts.item(0)
        skText1 = sk.sketchTexts.item(1)

        with open(input_file_path, 'r') as file:
            for name in file:
                word = name.strip().split()
                if len(word) == 1:
                    skText.text = skText1.text = name.strip()
                elif len(word) == 2:
                    skText.text = word[0]
                    skText1.text = word[1]

                filename = os.path.join(output_folder_path, f'{name.strip()}.stl')
                exportMgr = adsk.fusion.ExportManager.cast(design.exportManager)
                stlOptions = exportMgr.createSTLExportOptions(rootComp)
                stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
                stlOptions.filename = filename
                exportMgr.execute(stlOptions)
    except:
        ui.messageBox(f'Failed:\n{traceback.format_exc()}')

def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []
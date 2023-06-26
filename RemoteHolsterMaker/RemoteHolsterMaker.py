# Author- Jamie Smith
# Description- Make a remote holster
#
import math
from typing import Tuple
# import sys
# sys.path.append("/Users/jamie/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Python/defs")
import adsk.core, adsk.fusion, adsk.cam, traceback

# Some Constants
#
# Don't know why this is here
SCALE = 0.1

# Default Values
#
defaultHolsterName = "Holster"
defaultRemoteWidth = 80.0
defaultRemoteLength = 44.0
defaultRemoteThickness = 15.0
defaultFrontSlotWidth = 10.0
defaultFrontHeight = 22.0
defaultBackCornerRound = 4.0
defaultFillet = 0.5
defaultFrontSlotRound = 3.0
defaultSideThickness = 3.0
defaultBackThickness = 3.0
defaultBottomThickness = 3.0
defaultTolerance = 0.5

# Actual values
holsterName = defaultHolsterName
remoteWidth = defaultRemoteWidth * SCALE
remoteLength = defaultRemoteLength * SCALE
remoteThickness = defaultRemoteThickness * SCALE
frontSlotWidth = defaultFrontSlotWidth * SCALE
frontHeight = defaultFrontHeight * SCALE
backCornerRound = defaultBackCornerRound * SCALE
fillet = defaultFillet * SCALE
frontSlotRound = defaultFrontSlotRound * SCALE
sideThickness = defaultSideThickness * SCALE
backThickness = defaultBackThickness * SCALE
bottomThickness = defaultBottomThickness * SCALE
tolerance = defaultTolerance * SCALE

# global set of event handlers to keep them referenced for the duration of the command
handlers = []
app = adsk.core.Application.get()
if app:
    ui = app.userInterface

newComp = None

# Consts
CUT = adsk.fusion.FeatureOperations.CutFeatureOperation
JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
NEW_BODY = adsk.fusion.FeatureOperations.NewBodyFeatureOperation

def createComponent(design: adsk.fusion.Design, name: str) -> adsk.fusion.Component:
    rootComp = design.rootComponent
    allOccs = rootComp.occurrences
    newOcc = allOccs.addNewComponent(adsk.core.Matrix3D.create())
    comp = newOcc.component
    comp.name = name
    return comp

def createPoint(x: float, y: float, z: float) -> adsk.core.Point3D:
    return adsk.core.Point3D.create(x, y, z)

def create2DPoint(x, y):
    return createPoint(x, y, 0)

def createDistance(d) -> adsk.core.ValueInput:
    return adsk.core.ValueInput.createByReal(d)

def createReal(r) -> adsk.core.ValueInput:
    return adsk.core.ValueInput.createByReal(r)

def close(a, b):
    return abs(a - b) < 1e-5 * SCALE

# Some basic utility commands
#
def createBaseRectSketch(component: adsk.fusion.Component, holster) -> adsk.fusion.Profile:
    base_sketch = component.sketches.add(component.xYConstructionPlane)
    base_sketch.name = "Base Sketch"
    p0 = create2DPoint(0, 0)
    p1 = create2DPoint((holster.remoteWidth + 2 * holster.sideThickness) * SCALE, (holster.remoteThickness + holster.sideThickness + holster.backThickness) * SCALE)
    base_rect = base_sketch.sketchCurves.sketchLines.addTwoPointRectangle(p0, p1)
    # FIXME: there must be a better way!
    base_rect_profile = base_sketch.profiles.item(0)
    return base_rect_profile

def createCurvedRect(component: adsk.fusion.Component, name, width: float, depth: float, radius: float, z: float) -> Tuple[adsk.core.ObjectCollection, adsk.fusion.Profile]:
    path = adsk.core.ObjectCollection.create()
    sketch: adsk.fusion.Sketch = component.sketches.add(component.xZConstructionPlane)
    sketch.name = name
    lines = sketch.sketchCurves.sketchLines
    p = lambda x, y: createPoint(x, y , z)

    p0 = p(radius, 0)
    p1 = p(width - radius, 0)
    l0 = lines.addByTwoPoints(p0, p1)
    p2 = p(width, radius)
    p3 = p(width, depth - radius)
    l1 = lines.addByTwoPoints(p2, p3)
    p4 = p(width - radius, depth)
    p5 = p(radius, depth)
    l2 = lines.addByTwoPoints(p4, p5)
    p6 = p(0, depth - radius)
    p7 = p(0, radius)
    l3 = lines.addByTwoPoints(p6, p7)

    arcs = sketch.sketchCurves.sketchArcs

    p7c = p(radius, radius)
    a0 = arcs.addByCenterStartSweep(p7c, p7, math.pi / 2)
    # FIXME: you'd've thought all these merges made a single thing. You'd be wrong.
    # The arcs end up joined to the lines they were started on but the merges do nothing.
    #a0.endSketchPoint.merge(l0.startSketchPoint)
    #path.add(a0)
    p1c = p(width - radius, radius)
    a1 = arcs.addByCenterStartSweep(p1c, p1, math.pi / 2)
    #a1.endSketchPoint.merge(l1.startSketchPoint)
    #path.add(a1)
    p3c = p(width - radius, depth - radius)
    a2 = arcs.addByCenterStartSweep(p3c, p3, math.pi / 2)
    #a2.endSketchPoint.merge(l2.startSketchPoint)
    #path.add(a2)
    p5c = p(radius, depth - radius)
    a3 = arcs.addByCenterStartSweep(p5c, p5, math.pi / 2)
    #a3.endSketchPoint.merge(l3.startSketchPoint)
    #path.add(a3)

    # These have to be in exactly the right order
    path.add(l3)
    path.add(a3)
    path.add(l2)
    path.add(a2)
    path.add(l1)
    path.add(a1)
    path.add(l0)
    path.add(a0)

    # FIXME: not actually a path
    return path, sketch.profiles.item(0)

# def createBaseSweepSketch(component: adsk.fusion.Component) -> adsk.core.ObjectCollection:
#     b, _ = createCurvedRect(component,  "Base Sweep Sketch", slotDimension, slotDimension, baseCornerRadius, 0)
#     return b

class HolsterCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            unitsMgr = app.activeProduct.unitsManager
            command = args.firingEvent.sender
            inputs = command.commandInputs

            holster = Holster()
            
            for input in inputs:
                if input.id == 'holsterName':
                    holster.holsterName = input.value
                elif input.id == 'remoteWidth':
                    holster.remoteWidth = input.value
                elif input.id == 'remoteLength':
                    holster.remoteLength = input.value
                elif input.id == 'remoteThickness':
                    holster.remoteThickness = input.value
                elif input.id == 'frontSlotWidth':
                    holster.frontSlotWidth = input.value
                elif input.id == 'frontHeight':
                    holster.frontHeight = input.value
                elif input.id == 'backCornerRound':
                    holster.backCornerRound = input.value
                elif input.id == 'fillet':
                    holster.fillet = input.value
                elif input.id == 'frontSlotRound':
                    holster.frontSlotRound = input.value
                elif input.id == 'sideThickness':
                    holster.sideThickness = input.value                
                elif input.id == 'backThickness':
                    holster.backThickness = input.value                
                elif input.id == 'bottomThickness':
                    holster.bottomThickness = input.value                
                elif input.id == 'tolerance':
                    holster.tolerance = input.value                
             
            holster.buildHolster();
            
            args.isValidResult = True

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class HolsterCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # when the command is done, terminate the script
            # this will release all globals which will remove all event handlers
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class HolsterCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):    
    def __init__(self):
        super().__init__()        
    def notify(self, args):
        try:
            cmd = args.command
            cmd.isRepeatable = False
            onExecute = HolsterCommandExecuteHandler()
            cmd.execute.add(onExecute)
            onExecutePreview = HolsterCommandExecuteHandler()
            cmd.executePreview.add(onExecutePreview)
            onDestroy = HolsterCommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            # keep the handler referenced beyond this function
            handlers.append(onExecute)
            handlers.append(onExecutePreview)
            handlers.append(onDestroy)

            #define the inputs
            inputs = cmd.commandInputs
            
            finestIncrement = 1.0
            
            # JRS: These values / ranges are not set
            # 
            inputs.addStringValueInput('holsterName', 'Holster Name', defaultHolsterName)
             
            initRemoteWidth = adsk.core.ValueInput.createByReal(defaultRemoteWidth)
            inputs.addFloatSpinnerCommandInput('remoteWidth', 'Remote Width', '', 0.25, 100.0, finestIncrement, defaultRemoteWidth)

            initremoteLength = adsk.core.ValueInput.createByReal(defaultRemoteLength)
            inputs.addFloatSpinnerCommandInput('remoteLength', 'Remote Height', '', 0.25, 100.0, finestIncrement, defaultRemoteLength)

            initRemoteThickness = adsk.core.ValueInput.createByReal(defaultRemoteThickness)
            inputs.addFloatSpinnerCommandInput('remoteThickness', 'Remote Thickness', '', 0.25, 100.0, finestIncrement, defaultRemoteThickness)

            initFrontHeight = adsk.core.ValueInput.createByReal(defaultFrontHeight)
            inputs.addFloatSpinnerCommandInput('frontHeight', 'Front Height', '', 0.25, 100.0, finestIncrement, defaultFrontHeight)

            initFrontSlotWidth = adsk.core.ValueInput.createByReal(defaultFrontSlotWidth)
            inputs.addFloatSpinnerCommandInput('frontSlotWidth', 'Front Slot Width', '', 0.25, 100.0, finestIncrement, defaultFrontSlotWidth)

            initBackCornerRound = adsk.core.ValueInput.createByReal(defaultBackCornerRound)
            inputs.addFloatSpinnerCommandInput('backCornerRound', 'Back Corner Round', '', 0.25, 100.0, finestIncrement, defaultBackCornerRound)

            initFillet = adsk.core.ValueInput.createByReal(defaultFillet)
            inputs.addFloatSpinnerCommandInput('fillet', 'Overall Fillet', '', 0.25, 100.0, 0.01, defaultFillet)

            initFrontSlotRound = adsk.core.ValueInput.createByReal(defaultFrontSlotRound)
            inputs.addFloatSpinnerCommandInput('frontSlotRound', 'Front Slot Round', '', 0.25, 100.0, finestIncrement, defaultFrontSlotRound)

            initSideThickness = adsk.core.ValueInput.createByReal(defaultSideThickness)
            inputs.addFloatSpinnerCommandInput('sideThickness', 'Side Thickness', '', 0.25, 100.0, finestIncrement, defaultSideThickness)

            initBackThickness = adsk.core.ValueInput.createByReal(defaultBackThickness)
            inputs.addFloatSpinnerCommandInput('backThickness', 'Back Thickness', '', 0.25, 100.0, finestIncrement, defaultBackThickness)

            initBottomThickness = adsk.core.ValueInput.createByReal(defaultBottomThickness)
            inputs.addFloatSpinnerCommandInput('bottomThickness', 'Bottom Thickness', '', 0.25, 100.0, finestIncrement, defaultBottomThickness)

            initTolerance = adsk.core.ValueInput.createByReal(defaultTolerance)
            inputs.addFloatSpinnerCommandInput('tolerance', 'Tolerance', '', 0.25, 100.0, finestIncrement, defaultTolerance)

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class Holster:
    def __init__(self):
        self._holsterName = defaultHolsterName
        self._remoteWidth = defaultRemoteWidth
        self._remoteLength = defaultRemoteLength
        self._remoteThickness = defaultRemoteThickness
        self._frontSlotWidth = defaultFrontSlotWidth
        self._frontHeight = defaultFrontHeight
        self._backCornerRound = defaultBackCornerRound
        self._fillet = defaultFillet
        self._frontSlotRound = defaultFrontSlotRound
        self._sideThickness = defaultSideThickness
        self._backThickness = defaultBackThickness
        self._bottomThickness = defaultBottomThickness
        self._tolerance = defaultTolerance

    # properties
    #
    @property
    def holsterName(self):
        return self._holsterName
    @holsterName.setter
    def holsterName(self, value):
        self._holsterName = value

    @property
    def remoteWidth(self):
        return self._remoteWidth
    @remoteWidth.setter
    def remoteWidth(self, value):
        self._remoteWidth = value

    @property
    def remoteLength(self):
        return self._remoteLength
    @remoteLength.setter
    def remoteLength(self, value):
        self._remoteLength = value

    @property
    def remoteThickness(self):
        return self._remoteThickness
    @remoteThickness.setter
    def remoteThickness(self, value):
        self._remoteThickness = value

    @property
    def frontSlotWidth(self):
        return self._frontSlotWidth
    @frontSlotWidth.setter
    def frontSlotWidth(self, value):
        self._frontSlotWidth = value

    @property
    def frontHeight(self):
        return self._frontHeight
    @frontHeight.setter
    def frontHeight(self, value):
        self._frontHeight = value

    @property
    def backCornerRound(self):
        return self._backCornerRound
    @backCornerRound.setter
    def backCornerRound(self, value):
        self._backCornerRound = value

    @property
    def fillet(self):
        return self._fillet
    @fillet.setter
    def fillet(self, value):
        self._fillet = value

    @property
    def frontSlotRound(self):
        return self._frontSlotRound
    @frontSlotRound.setter
    def frontSlotRound(self, value):
        self._frontSlotRound = value

    @property
    def sideThickness(self):
        return self._sideThickness
    @sideThickness.setter
    def sideThickness(self, value):
        self._sideThickness = value
        
    @property
    def backThickness(self):
        return self._backThickness
    @backThickness.setter
    def backThickness(self, value):
        self._backThickness = value

    @property
    def bottomThickness(self):
        return self._bottomThickness
    @bottomThickness.setter
    def bottomThickness(self, value):
        self._bottomThickness = value

    @property
    def tolerance(self):
        return self._tolerance
    @tolerance.setter
    def tolerance(self, value):
        self._tolerance = value


    def buildHolster(self):
        try:
            # Get the active design.
            app = adsk.core.Application.get()
            product = app.activeProduct
            design = adsk.fusion.Design.cast(product)
            ui = app.userInterface

            global component
            
            # Units
            design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits

            # Main component
            component = createComponent(design, self.holsterName)
            
            if component is None:
                ui.messageBox('New component failed to create', 'New Component Failed')
                return
            
            # This is the flow of how I built the holster by hand
            #
            # 1) create the base rectangle on the XY plane, (remoteWidth + 2*sideThickness) x (remoteThickness + sideThickness + backThickness)
            # 2) extrude that rectangle to the remoteLength + bottomThickness
            # 3) add rectangle of side thickness (OK, not exactly- could have a different back thickness)
            # 4) extrude that offset to remoteLength (leaving BottomThickness)
            # Sketch base
            base_rect_profile = createBaseRectSketch(component, self)
            distance = createDistance((self.remoteLength + self.bottomThickness) * SCALE)
            # ui.messageBox("Dimensions %s x %s x %s" % (str(self.remoteLength), str(self.remoteWidth), str(self.remoteThickness)))
            
            # Extrude to full height
            #
            holster = component.features.extrudeFeatures.addSimple(base_rect_profile, distance, NEW_BODY)
            holster_body = holster.bodies.item(0)
            holster_body.name = "Holster"
            
            # Cut out the pocket
            #
            pocket_profile = createPocketSketch(component, self)            
            pocket_depth = createDistance(self.remoteLength * SCALE * -1)
            component.features.extrudeFeatures.addSimple(pocket_profile, pocket_depth, CUT)

            # Push down the front
            #
            front_profile = createFrontSketch(component, self)            
            front_depth = createDistance((self.remoteLength - self.frontHeight) * SCALE * -1)
            component.features.extrudeFeatures.addSimple(front_profile, front_depth, CUT)

            # Create Slot
            #
            slot_profile = createSlotSketch(component, self)
            slot_depth = createDistance((self.remoteThickness + self.sideThickness) * SCALE)
            component.features.extrudeFeatures.addSimple(slot_profile, slot_depth, CUT)
            
            e = holster_body.edges
           
            fillet_edges = adsk.core.ObjectCollection.create()
            for n in range(e.count):
                edge = e.item(n)
                bb = edge.boundingBox
                mx = bb.maxPoint
                mn = bb.minPoint
                fillet_edges.add(edge)

            fillets = component.features.filletFeatures
            fillet_input = fillets.createInput()
            fillet_radius = createDistance(self.fillet * SCALE)
            fillet_input.addConstantRadiusEdgeSet(fillet_edges, fillet_radius, True)
            fillet_input.isG2 = False
            fillet_input.isRollingBallCorner = True
            top_fillet = fillets.add(fillet_input)
        except:
            if ui:
                ui.messageBox('Failed to compute the holster. This is most likely because the input values define an invalid holster.')
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def createPocketSketch(component: adsk.fusion.Component, holster) -> adsk.core.ObjectCollection:
    sketch: adsk.fusion.Sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = "Pocket Sketch"
    
    p1 = createPoint((holster.sideThickness) * SCALE, (holster.sideThickness) * SCALE, (holster.remoteLength + holster.bottomThickness) * SCALE)
    p2 = createPoint((holster.sideThickness + holster.remoteWidth) * SCALE, (holster.sideThickness + holster.remoteThickness) * SCALE, (holster.remoteLength + holster.bottomThickness) * SCALE)

    sketch.sketchCurves.sketchLines.addTwoPointRectangle(p1, p2)

    rect = adsk.core.ObjectCollection.create()
    rect.add(sketch.profiles.item(0))

    return rect
            
def createFrontSketch(component: adsk.fusion.Component, holster) -> adsk.core.ObjectCollection:
    sketch: adsk.fusion.Sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = "Front Sketch"
    
    p1 = createPoint(0, 0, (holster.remoteLength + holster.bottomThickness) * SCALE)
    p2 = createPoint((2 * holster.sideThickness + holster.remoteWidth) * SCALE, (holster.sideThickness + holster.remoteThickness) * SCALE, (holster.remoteLength + holster.bottomThickness) * SCALE)

    sketch.sketchCurves.sketchLines.addTwoPointRectangle(p1, p2)

    rect = adsk.core.ObjectCollection.create()
    rect.add(sketch.profiles.item(0))

    return rect

def createSlotSketch(component: adsk.fusion.Component, holster) -> adsk.core.ObjectCollection:
    sketch: adsk.fusion.Sketch = component.sketches.add(component.xZConstructionPlane)
    sketch.name = "Slot Sketch"
    slotLeft = (holster.sideThickness + holster.remoteWidth - holster.frontSlotWidth)/2
    p1 = createPoint(slotLeft * SCALE, 0, 0)
    p2 = createPoint((slotLeft + holster.frontSlotWidth) * SCALE, -1 * (holster.frontHeight + holster.bottomThickness) * SCALE, 0)

    sketch.sketchCurves.sketchLines.addTwoPointRectangle(p1, p2)
   
    rect = adsk.core.ObjectCollection.create()
    rect.add(sketch.profiles.item(0))

    return rect

def run(context):
    try:
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox('It is not supported in current workspace, please change to MODEL workspace and try again.')
            return
        commandDefinitions = ui.commandDefinitions
        
        #check the command exists or not
        #
        cmdDef = commandDefinitions.itemById('RemoteHolster')
        if not cmdDef:
            cmdDef = commandDefinitions.addButtonDefinition('RemoteHolster',
                    'Create a Remote Holster',
                    'Create a Remote Holster.')

        onCommandCreated = HolsterCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        # keep the handler referenced beyond this function
        handlers.append(onCommandCreated)
        inputs = adsk.core.NamedValues.create()
        
        cmdDef.execute(inputs)

        # prevent this module from being terminate when the script returns, because we are waiting for event handlers to fire
        adsk.autoTerminate(False)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

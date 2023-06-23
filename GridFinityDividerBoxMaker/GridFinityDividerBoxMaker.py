#Author- Ben Laurie <ben@links.org>
#Description- Make gridfinity divider boxes

import math
from typing import Tuple
import adsk.core, adsk.fusion, adsk.cam, traceback

# Foot is 6mm high
#
defaultBoxName = "Box"
defaultSlotsWide = 2
defaultSlotsDeep = 2

# 52" Husky case 
#
defaultSlotsHigh = 1.45

# 62" Husky case 
#
# defaultSlotsHigh = 1.25

defaultDividerCount = 0
defaultBaseOnly = False
defaultIncludeScoop = True
defaultIncludeLedge = True
defaultIncludeMagnets = False

# global set of event handlers to keep them referenced for the duration of the command
handlers = []
app = adsk.core.Application.get()
if app:
    ui = app.userInterface

newComp = None

# Why?
SCALE = 0.1

magnetDiameter = 6.5 * SCALE * 0.75
magnetThickness = 2.5 * SCALE * 0.75

# Sizes!
baseCornerRadius = 4 * SCALE
baseLip = .8 * SCALE
slotDimension = 42 * SCALE
nestingDepth = 5 * SCALE
nestingRimWidth = 2.4 * SCALE
nestingClearance = .25 * SCALE
wallThickness = 1.2 * SCALE
holeOffset = 8 * SCALE
ledgeOffset = 0.2 * SCALE

# Derived sizes
nestingVerticalClearance = nestingClearance * 1.416  # Empirically determined from original sketch

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


def createBaseRectSketch(component: adsk.fusion.Component) -> adsk.fusion.Profile:
    base_sketch = component.sketches.add(component.xZConstructionPlane)
    base_sketch.name = "Base Sketch"
    p0 = create2DPoint(0, 0)
    p1 = create2DPoint(slotDimension, slotDimension)
    base_rect = base_sketch.sketchCurves.sketchLines.addTwoPointRectangle(p0, p1)
    # FIXME: there must be a better way!
    base_rect_profile = base_sketch.profiles.item(0)
    return base_rect_profile

def createMagnetHolesSketch(component: adsk.fusion.Component) -> adsk.core.ObjectCollection:
    sketch: adsk.fusion.Sketch = component.sketches.add(component.xZConstructionPlane)
    sketch.name = "Magnet Holes Sketch"
    sketch.sketchCurves.sketchCircles.addByCenterRadius(createPoint(holeOffset, holeOffset, 0), magnetDiameter / 2.)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(createPoint(slotDimension - holeOffset, holeOffset, 0), magnetDiameter / 2.)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(createPoint(slotDimension - holeOffset, slotDimension - holeOffset, 0), magnetDiameter / 2.)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(createPoint(holeOffset, slotDimension - holeOffset, 0), magnetDiameter / 2.)

    circles = adsk.core.ObjectCollection.create()
    for n in range(4):
        circles.add(sketch.profiles.item(n))

    return circles

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


def createBaseSweepSketch(component: adsk.fusion.Component) -> adsk.core.ObjectCollection:
    b, _ = createCurvedRect(component,  "Base Sweep Sketch", slotDimension, slotDimension, baseCornerRadius, 0)
    return b

# Note that this attempts to combins the new bodies with the original to give a single body - this only works if they touch
def rectPattern(body: adsk.fusion.BRepBody, wide: int, deep: int, dim: float) -> adsk.fusion.RectangularPatternFeature:
    inputs = adsk.core.ObjectCollection.create()
    inputs.add(body)

    q0 = createReal(wide)
    q1 = createReal(deep)
    d0 = createDistance(dim)
    d1 = createDistance(-dim)

    component = body.parentComponent
    rectangularPatterns = component.features.rectangularPatternFeatures
    rectangularPatternInput = rectangularPatterns.createInput(inputs, component.xConstructionAxis, q0, d0, adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
    rectangularPatternInput.setDirectionTwo(component.zConstructionAxis, q1, d1)
    pattern = rectangularPatterns.add(rectangularPatternInput)

    # Attempt to combine everything into the original body
    tools = adsk.core.ObjectCollection.create()
    c = component.bRepBodies.count
    for n in range(c - (wide * deep) + 1, c):
        tools.add(component.bRepBodies.item(n))

    combineFeatures = component.features.combineFeatures
    combineFeaturesInput = combineFeatures.createInput(body, tools)
    combineFeaturesInput.operation = JOIN
    combineFeatures.add(combineFeaturesInput)

    return pattern

def createRimSketch(component: adsk.fusion.Component, slotsHigh) -> adsk.fusion.Profile:
    cornerVerticalOffset = nestingClearance * .416  # Empirically determined from existing sketch
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = "Rim Sketch"
    lines = sketch.sketchCurves.sketchLines
    h = -slotDimension / 2
    p = lambda x, y: createPoint(x, y , h)

    p0 = p(0, slotsHigh * slotDimension)
    p1 = p(0, slotsHigh * slotDimension + nestingDepth - nestingVerticalClearance)
    lines.addByTwoPoints(p0, p1)
    p2 = p(nestingRimWidth - nestingVerticalClearance, slotsHigh * slotDimension + nestingDepth - nestingRimWidth - cornerVerticalOffset)
    lines.addByTwoPoints(p1, p2)
    p3 = p(nestingRimWidth - nestingVerticalClearance, slotsHigh * slotDimension + baseLip - cornerVerticalOffset)
    lines.addByTwoPoints(p2, p3)
    p4 = p(nestingRimWidth + baseLip - nestingVerticalClearance, slotsHigh * slotDimension)
    lines.addByTwoPoints(p3, p4)
    lines.addByTwoPoints(p4, p0)

    return sketch.profiles.item(0)

def createIndentSketch(component: adsk.fusion.Component, slotsHigh) -> adsk.fusion.Profile:
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = "Indent Sketch"
    lines = sketch.sketchCurves.sketchLines
    h = -slotDimension / 2
    p = lambda x, y: createPoint(x, y , h)

    # Note that this is wallThickness below p4 in createRimSketch
    x = nestingRimWidth + baseLip - nestingVerticalClearance
    p0 = p(x, slotsHigh * slotDimension - wallThickness)
    p1 = p(x - wallThickness, slotsHigh * slotDimension - 2 * wallThickness)
    lines.addByTwoPoints(p0, p1)
    p2 = p(x - wallThickness, nestingDepth + wallThickness + 1 * SCALE)
    # FIXME: fillet this edge
    lines.addByTwoPoints(p1, p2)
    p3 = p(x, nestingDepth + wallThickness + 1 * SCALE)
    lines.addByTwoPoints(p2, p3)
    lines.addByTwoPoints(p3, p0)

    return sketch.profiles.item(0)

def createLedgeSketch(component: adsk.fusion.Component, slotsHigh) -> adsk.fusion.Profile:
    angle = 54

    sketch: adsk.fusion.Sketch = component.sketches.add(component.yZConstructionPlane)
    sketch.name = "Ledge Sketch"
    lines = sketch.sketchCurves.sketchLines
    h = wallThickness
    p = lambda x, y: createPoint(x, y , h)

    y = slotDimension * slotsHigh - ledgeOffset
    p0 = p(wallThickness, y)
    p1 = p(wallThickness + 16 * SCALE, y)
    lines.addByTwoPoints(p0, p1)
    d = math.sin(angle * math.pi / 180) * 16 * SCALE
    p2 = p(wallThickness, y - d)
    lines.addByTwoPoints(p1, p2)
    lines.addByTwoPoints(p2, p0)

    return sketch.profiles.item(0)
    
def createDividerSketch(component: adsk.fusion.Component, pos: float, slotsHigh, slotsDeep) -> adsk.fusion.Profile:
    sketch: adsk.fusion.Sketch = component.sketches.add(component.yZConstructionPlane)
    lines = sketch.sketchCurves.sketchLines
    p = lambda x, y: createPoint(x, y, pos)

    p0 = p(0, nestingDepth)
    p1 = p(slotsDeep * slotDimension, nestingDepth)
    lines.addByTwoPoints(p0, p1)
    p2 = p(slotsDeep * slotDimension, slotsHigh * slotDimension - ledgeOffset)
    lines.addByTwoPoints(p1, p2)
    p3 = p(0, slotsHigh * slotDimension - ledgeOffset)
    lines.addByTwoPoints(p2, p3)
    lines.addByTwoPoints(p3, p0)

    return sketch.profiles.item(0)    

class BoxCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            unitsMgr = app.activeProduct.unitsManager
            command = args.firingEvent.sender
            inputs = command.commandInputs

            box = Box()
            for input in inputs:
                if input.id == 'boxName':
                    box.boxName = input.value
                elif input.id == 'slotsWide':
                    box.slotsWide = input.value
                elif input.id == 'slotsDeep':
                    box.slotsDeep = input.value
                elif input.id == 'slotsHigh':
                    box.slotsHigh = input.value
                    # ui.messageBox(str(box.slotsHigh))
                elif input.id == 'dividerCount':
                    box.dividerCount = input.value
                elif input.id == 'includeScoop':
                    box.includeScoop = input.value
                elif input.id == 'baseOnly':
                    box.baseOnly = input.value
                elif input.id == 'includeLedge':
                    box.includeLedge = input.value
                elif input.id == 'includeMagnets':
                    box.includeMagnets = input.value

            box.buildBox();
            
            args.isValidResult = True

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class BoxCommandDestroyHandler(adsk.core.CommandEventHandler):
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

class BoxCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):    
    def __init__(self):
        super().__init__()        
    def notify(self, args):
        try:
            cmd = args.command
            cmd.isRepeatable = False
            onExecute = BoxCommandExecuteHandler()
            cmd.execute.add(onExecute)
            onExecutePreview = BoxCommandExecuteHandler()
            cmd.executePreview.add(onExecutePreview)
            onDestroy = BoxCommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            # keep the handler referenced beyond this function
            handlers.append(onExecute)
            handlers.append(onExecutePreview)
            handlers.append(onDestroy)

            #define the inputs
            inputs = cmd.commandInputs
            inputs.addStringValueInput('boxName', 'Box Name', defaultBoxName)
            
            initSlotsWide = adsk.core.ValueInput.createByReal(defaultSlotsWide)
            inputs.addIntegerSpinnerCommandInput('slotsWide', 'Slots Wide', 1, 20, 1, defaultSlotsWide)

            initSlotsDeep = adsk.core.ValueInput.createByReal(defaultSlotsDeep)
            inputs.addIntegerSpinnerCommandInput('slotsDeep', 'Slots Deep', 1, 20, 1, defaultSlotsDeep)
            
            # I'd love to make this just MMs
            initSlotsHigh = adsk.core.ValueInput.createByReal(defaultSlotsHigh)
            inputs.addFloatSpinnerCommandInput('slotsHigh', 'Slots High', '', 0.25, 10.0, 0.01, defaultSlotsHigh)

            initDividerCount = adsk.core.ValueInput.createByReal(defaultDividerCount)
            inputs.addIntegerSpinnerCommandInput('dividerCount', 'Divider Count', 0, 10, 1, defaultDividerCount)

            initIncludeScoop = adsk.core.ValueInput.createByReal(defaultIncludeScoop)
            inputs.addBoolValueInput('includeScoop', 'Include Scoop?', True, '', defaultIncludeScoop)

            initBaseOnly = adsk.core.ValueInput.createByReal(defaultBaseOnly)
            inputs.addBoolValueInput('baseOnly', 'Base Only?', True, '', defaultBaseOnly)

            initIncludeLedge = adsk.core.ValueInput.createByReal(defaultIncludeLedge)
            inputs.addBoolValueInput('includeLedge', 'Include Ledge?', True, '', defaultIncludeLedge)

            initIncludeMagnets = adsk.core.ValueInput.createByReal(defaultIncludeMagnets)
            inputs.addBoolValueInput('includeMagnets', 'Include Magnets?', True, '', defaultIncludeMagnets)

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class Box:
    def __init__(self):
        self._boxName = defaultBoxName
        self._slotsWide = defaultSlotsWide
        self._slotsDeep = defaultSlotsDeep
        self._slotsHigh = defaultSlotsHigh
        self._dividerCount = defaultDividerCount
        self._includeScoop = defaultIncludeScoop
        self._baseOnly = defaultBaseOnly
        self._includeLedge = defaultIncludeLedge
        self._includeMagnets = defaultIncludeMagnets

    #properties
    @property
    def boxName(self):
        return self._boxName
    @boxName.setter
    def boxName(self, value):
        self._boxName = value

    @property
    def slotsWide(self):
        return self._slotsWide
    @slotsWide.setter
    def slotsWide(self, value):
        self._slotsWide = value
        
    @property
    def slotsDeep(self):
        return self._slotsDeep
    @slotsDeep.setter
    def slotsDeep(self, value):
        self._slotsDeep = value

    @property
    def slotsHigh(self):
        return self._slotsHigh
    @slotsHigh.setter
    def slotsHigh(self, value):
        self._slotsHigh = value

    @property
    def dividerCount(self):
        return self._dividerCount
    @dividerCount.setter
    def dividerCount(self, value):
        self._dividerCount = value
        
    @property
    def includeScoop(self):
        return self._includeScoop
    @includeScoop.setter
    def includeScoop(self, value):
        self._includeScoop = value

    @property
    def baseOnly(self):
        return self._baseOnly
    @baseOnly.setter
    def baseOnly(self, value):
        self._baseOnly = value

    @property
    def includeLedge(self):
        return self._includeLedge
    @includeLedge.setter
    def includeLedge(self, value):
        self._includeLedge = value
        
    @property
    def includeMagnets(self):
        return self._includeMagnets
    @includeMagnets.setter
    def includeMagnets(self, value):
        self._includeMagnets = value
        
    def buildBox(self):
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
            component = createComponent(design, self.boxName)
            if component is None:
                ui.messageBox('New component failed to create', 'New Component Failed')
                return

            # Sketch base
            base_rect_profile = createBaseRectSketch(component)
            # Extrude
            distance = createDistance(nestingDepth)
            base = component.features.extrudeFeatures.addSimple(base_rect_profile, distance, NEW_BODY)
            base_body = base.bodies.item(0)
            base_body.name = "Base"

            if self.includeMagnets:
                # Magnet hole sketch
                magnet_holes_profile = createMagnetHolesSketch(component)

                # Extrude for magnets
                distance = createDistance(magnetThickness)
                component.features.extrudeFeatures.addSimple(magnet_holes_profile, distance, CUT)

            # Profile for the edge
            edge_sketch = component.sketches.add(component.xYConstructionPlane)
            edge_sketch.name = "Edge Profile Sketch"
            lines = edge_sketch.sketchCurves.sketchLines
            h = -slotDimension / 2
            p0 = createPoint(-1, 0, h)
            p1a = createPoint(-1, nestingDepth, h)
            lines.addByTwoPoints(p0, p1a)
            p1 = createPoint(0, nestingDepth, h)
            lines.addByTwoPoints(p1a, p1)
            p2 = createPoint(nestingRimWidth + baseLip, 0, h)
            lines.addByTwoPoints(p0, p2)
            p3 = createPoint(nestingRimWidth, baseLip, h)
            lines.addByTwoPoints(p2, p3)
            p4 = createPoint(nestingRimWidth, nestingDepth - nestingRimWidth, h)
            lines.addByTwoPoints(p1, p4)
            lines.addByTwoPoints(p4, p3)

            # FIXME: this really offends me!
            edge_profile = edge_sketch.profiles.item(0)

            # Path to sweep profile along (derived from baserect)
            sweep_path_objects = createBaseSweepSketch(component)
            sweep_path = component.features.createPath(sweep_path_objects)

            # Do the sweeps
            sweeps = component.features.sweepFeatures
            sweep_input = sweeps.createInput(edge_profile, sweep_path, CUT)
            sweep = sweeps.add(sweep_input)

            # Copy for the whole base
            if self.slotsWide > 1 or self.slotsDeep > 1:
                rectPattern(base_body, self.slotsWide, self.slotsDeep, slotDimension)

            # Now the box
            box_path_objects, box_profile = createCurvedRect(component, "Box Profile", self.slotsWide * slotDimension, self.slotsDeep * slotDimension, baseCornerRadius, nestingDepth)
            if self.baseOnly:
                distance = createDistance(1*SCALE)
                base = component.features.extrudeFeatures.addSimple(box_profile, distance, JOIN)
                return
                
            distance = createDistance(self.slotsHigh * slotDimension - nestingDepth)
            base = component.features.extrudeFeatures.addSimple(box_profile, distance, JOIN)

            # Rim
            rim_profile = createRimSketch(component, self.slotsHigh)
            box_path = component.features.createPath(box_path_objects)
            sweep_input = sweeps.createInput(rim_profile, box_path, JOIN)
            sweep = sweeps.add(sweep_input)

            # Put a fillet on the top edge
            e = base_body.edges
            top_edge = e.item(0)
            for n in range(e.count):
                edge = e.item(n)
                bb = edge.boundingBox
                mx = bb.maxPoint
                mn = bb.minPoint
                if mn.y > top_edge.boundingBox.minPoint.y:
                    #print(f'[{mn.x}, {mn.y}, {mn.z}] -> [{mx.x}, {mx.y}, {mx.z}]')
                    top_edge = edge
            fillet_edges = adsk.core.ObjectCollection.create()
            fillet_edges.add(top_edge)

            fillets = component.features.filletFeatures
            fillet_input = fillets.createInput()
            fillet_radius = createDistance(.6 * SCALE)
            fillet_input.addConstantRadiusEdgeSet(fillet_edges, fillet_radius, True)
            fillet_input.isG2 = False
            fillet_input.isRollingBallCorner = True
            top_fillet = fillets.add(fillet_input)

            # Make the hole in the box
            # Find the profile to extrude
            f = base_body.faces
            extrude_face = None
            count = 0
            for n in range(f.count):
                bb = f.item(n).boundingBox
                mx = bb.maxPoint
                mn = bb.minPoint
                if close(mn.y, self.slotsHigh * slotDimension) and close(mx.y, self.slotsHigh * slotDimension):
                    #print(f'[{mn.x}, {mn.y}, {mn.z}] -> [{mx.x}, {mx.y}, {mx.z}]')
                    count += 1
                    extrude_face = f.item(n)
            assert count == 1

            # And extrude it
            # FIXME: the + 1 * SCALE is ad hoc (but copied from the original)
            distance = createDistance(-(self.slotsHigh * slotDimension - (nestingDepth + wallThickness + 1 * SCALE)))
            component.features.extrudeFeatures.addSimple(extrude_face, distance, CUT)

            # Indent the lower part of the box to leave a rim around the top
            indent_profile = createIndentSketch(component, self.slotsHigh)
            sweep_input = sweeps.createInput(indent_profile, box_path, CUT)
            sweep = sweeps.add(sweep_input)

            if self.includeLedge and self.slotsHigh >= 0.43 :
                # Add the ledge
                ledge_profile = createLedgeSketch(component, self.slotsHigh)
                distance = createDistance(self.slotsWide * slotDimension - wallThickness * 2)
                component.features.extrudeFeatures.addSimple(ledge_profile, distance, JOIN)

            if self.includeScoop:
                # Add the curved scoop
                edges = base_body.edges
                ty = nestingDepth + wallThickness + 1 * SCALE
                #print(ty)
                fillet_edge = None
                count = 0
                for n in range(edges.count):
                    edge = edges.item(n)
                    bb = edge.boundingBox
                    mx = bb.maxPoint
                    mn = bb.minPoint
                    # FIXME: where does -8.2354 come from?
                    if close(mn.y, ty) and close(mx.y, ty) and close(mn.x, baseCornerRadius) and close(mx.x, self.slotsWide * slotDimension - baseCornerRadius) and close(mn.z, -(self.slotsDeep * slotDimension - .1646)):
                        #print(f'[{mn.x}, {mn.y}, {mn.z}] -> [{mx.x}, {mx.y}, {mx.z}]')
                        fillet_edge = edge
                        count += 1
                assert count == 1

                fillet_input = fillets.createInput()
                fillet_radius = createDistance(slotDimension * self.slotsHigh / 2)
                edges = adsk.core.ObjectCollection.create()
                edges.add(fillet_edge)
                fillet_input.addConstantRadiusEdgeSet(edges, fillet_radius, False)
                fillet_input.isG2 = False
                fillet_input.isRollingBallCorner = True
                fillets.add(fillet_input)

            # # Now we're a box. :-)
            base_body.name = self.boxName

            # Finally, dividers
            # FIXME: these end up not *quite* the same size
            l = self.slotsWide * slotDimension - 2 * wallThickness
            for n in range(self.dividerCount):
                y = (n + 1) * l / (self.dividerCount + 1) + wallThickness / 2
                divider_profile = createDividerSketch(component, y, slotsHigh=self.slotsHigh, slotsDeep=self.slotsDeep)
                distance = createDistance(wallThickness)
                divider = component.features.extrudeFeatures.addSimple(divider_profile, distance, JOIN)

                edges = adsk.core.ObjectCollection.create()
                #print(y)
                for n in range(divider.faces.count):
                    f = divider.faces.item(n)
                    bb = f.boundingBox
                    mx = bb.maxPoint
                    mn = bb.minPoint
                    if (close(mn.x, y) and close(mx.x, y)) or (close(mn.x, y +  wallThickness) and close(mx.x, y + wallThickness)):
                        #print(f'[{mn.x}, {mn.y}, {mn.z}] -> [{mx.x}, {mx.y}, {mx.z}]')
                        for e in range(f.edges.count):
                            edges.add(f.edges.item(e))
                fillet_input = fillets.createInput()
                fillet_radius = createDistance(.6 * SCALE)
                fillet_input.addConstantRadiusEdgeSet(edges, fillet_radius, True)
                fillet_input.isG2 = False
                fillet_input.isRollingBallCorner = True
                fillets.add(fillet_input)        
        except:
            if ui:
                ui.messageBox('Failed to compute the box. This is most likely because the input values define an invalid box.')
            
            
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
        cmdDef = commandDefinitions.itemById('GridfinityDividerBox')
        if not cmdDef:
            cmdDef = commandDefinitions.addButtonDefinition('GridfinityDividerBox',
                    'Create a Gridfinity Box',
                    'Create a Gridfinity Box.')

        onCommandCreated = BoxCommandCreatedHandler()
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

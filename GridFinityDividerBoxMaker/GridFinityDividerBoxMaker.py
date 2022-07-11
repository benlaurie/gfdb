#Author- Ben Laurie <ben@links.org>
#Description- Make gridfinity divider boxes

import math
from typing import Tuple
import adsk.core, adsk.fusion, adsk.cam, traceback

# Why?
SCALE = 0.1

# User parameters

ui = None
app = adsk.core.Application.get()
ui = app.userInterface

slotsWide = 2
input = '2'  # The initial default value.
isValid = False
while not isValid:
    retVals = ui.inputBox('Slots Wide', 'Count', input)
    if retVals[0]:
        (input, isCancelled) = retVals
    #if isCancelled:
    #    return
    try:
        slotsWide = int(input)
        isValid = True
    except:
        isValid = False


slotsDeep = 3
input = '3'  # The initial default value.
isValid = False
while not isValid:
    retVals = ui.inputBox('Slots Deep', 'Count', input)
    if retVals[0]:
        (input, isCancelled) = retVals
    #if isCancelled:
    #    return
    try:
        slotsDeep = int(input)
        isValid = True
    except:
        isValid = False

slotsHigh = 1.5
input = '1.5'  # The initial default value.
isValid = False
while not isValid:
    retVals = ui.inputBox('Slots High', 'Count', input)
    if retVals[0]:
        (input, isCancelled) = retVals
    #if isCancelled:
    #    return
    try:
        slotsHigh = float(input)
        isValid = True
    except:
        isValid = False

input = '5'  # The initial default value.
dividerCount = 5
isValid = False
while not isValid:
    retVals = ui.inputBox('Enter divider count', 'Count', input)
    if retVals[0]:
        (input, isCancelled) = retVals
    #if isCancelled:
    #    return
    try:
        dividerCount = int(input)
        isValid = True
    except:
        isValid = False
magnetDiameter = 6.5 * SCALE
magnetThiccness = 2.5 * SCALE

# Sizes!
# FIXME: make these strings, e.g. "42 mm" (maybe, some contexts that's not right for)
baseCornerRadius = 4 * SCALE
baseLip = .8 * SCALE
slotDimension = 42 * SCALE
nestingDepth = 5 * SCALE
nestingRimWidth = 2.4 * SCALE
nestingClearance = .25 * SCALE
wallThiccness = 1.2 * SCALE
holeOffset = 8 * SCALE

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

# Geometry

def createBaseRectSketch(component: adsk.fusion.Component) -> adsk.fusion.Profile:
    base_sketch = component.sketches.add(component.xZConstructionPlane)
    p0 = create2DPoint(0, 0)
    p1 = create2DPoint(slotDimension, slotDimension)
    base_rect = base_sketch.sketchCurves.sketchLines.addTwoPointRectangle(p0, p1)
    # FIXME: there must be a better way!
    base_rect_profile = base_sketch.profiles.item(0)
    return base_rect_profile

def createMagnetHolesSketch(component: adsk.fusion.Component) -> adsk.core.ObjectCollection:
    sketch: adsk.fusion.Sketch = component.sketches.add(component.xZConstructionPlane)
    
    sketch.sketchCurves.sketchCircles.addByCenterRadius(createPoint(holeOffset, holeOffset, 0), magnetDiameter / 2.)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(createPoint(slotDimension - holeOffset, holeOffset, 0), magnetDiameter / 2.)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(createPoint(slotDimension - holeOffset, slotDimension - holeOffset, 0), magnetDiameter / 2.)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(createPoint(holeOffset, slotDimension - holeOffset, 0), magnetDiameter / 2.)

    circles = adsk.core.ObjectCollection.create()
    for n in range(4):
        circles.add(sketch.profiles.item(n))

    return circles

def createCurvedRect(component: adsk.fusion.Component, width: float, depth: float, radius: float, z: float) -> Tuple[adsk.core.ObjectCollection, adsk.fusion.Profile]:
    path = adsk.core.ObjectCollection.create()
    sketch: adsk.fusion.Sketch = component.sketches.add(component.xZConstructionPlane)
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
    b, _ = createCurvedRect(component, slotDimension, slotDimension, baseCornerRadius, 0)
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

def createRimSketch(component: adsk.fusion.Component) -> adsk.fusion.Profile:
    cornerVerticalOffset = nestingClearance * .416  # Empirically determined from existing sketch
    sketch = component.sketches.add(component.xYConstructionPlane)
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

def createIndentSketch(component: adsk.fusion.Component) -> adsk.fusion.Profile:
    sketch = component.sketches.add(component.xYConstructionPlane)
    lines = sketch.sketchCurves.sketchLines
    h = -slotDimension / 2
    p = lambda x, y: createPoint(x, y , h)

    # Note that this is wallThiccness below p4 in createRimSketch
    x = nestingRimWidth + baseLip - nestingVerticalClearance
    p0 = p(x, slotsHigh * slotDimension - wallThiccness)
    p1 = p(x - wallThiccness, slotsHigh * slotDimension - 2 * wallThiccness)
    lines.addByTwoPoints(p0, p1)
    p2 = p(x - wallThiccness, nestingDepth + wallThiccness + 1 * SCALE)
    # FIXME: fillet this edge
    lines.addByTwoPoints(p1, p2)
    p3 = p(x, nestingDepth + wallThiccness + 1 * SCALE)
    lines.addByTwoPoints(p2, p3)
    lines.addByTwoPoints(p3, p0)

    return sketch.profiles.item(0)

def createLedgeSketch(component: adsk.fusion.Component) -> adsk.fusion.Profile:
    angle = 54

    sketch: adsk.fusion.Sketch = component.sketches.add(component.yZConstructionPlane)
    lines = sketch.sketchCurves.sketchLines
    h = wallThiccness * 2
    p = lambda x, y: createPoint(x, y , h)

    y = slotDimension * slotsHigh
    p0 = p(wallThiccness, y)
    p1 = p(wallThiccness + 16 * SCALE, y)
    lines.addByTwoPoints(p0, p1)
    d = math.sin(angle * math.pi / 180) * 16 * SCALE
    p2 = p(wallThiccness, y - d)
    lines.addByTwoPoints(p1, p2)
    lines.addByTwoPoints(p2, p0)

    return sketch.profiles.item(0)

def createDividerSketch(component: adsk.fusion.Component, pos: float) -> adsk.fusion.Profile:
    sketch: adsk.fusion.Sketch = component.sketches.add(component.yZConstructionPlane)
    lines = sketch.sketchCurves.sketchLines
    p = lambda x, y: createPoint(x, y, pos)

    p0 = p(0, nestingDepth)
    p1 = p(slotsDeep * slotDimension, nestingDepth)
    lines.addByTwoPoints(p0, p1)
    p2 = p(slotsDeep * slotDimension, slotsHigh * slotDimension)
    lines.addByTwoPoints(p1, p2)
    p3 = p(0, slotsHigh * slotDimension)
    lines.addByTwoPoints(p2, p3)
    lines.addByTwoPoints(p3, p0)

    return sketch.profiles.item(0)


def run(context):
    # Get the active design.
    app = adsk.core.Application.get()
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)

    # Units
    design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits

    # Main component
    component = createComponent(design, "Divider Box")

    # Sketch base
    base_rect_profile = createBaseRectSketch(component)
    # Extrude
    distance = createDistance(nestingDepth)
    base = component.features.extrudeFeatures.addSimple(base_rect_profile, distance, NEW_BODY)
    base_body = base.bodies.item(0)
    base_body.name = "Base"

    # Magnet holes
    magnet_holes_profile = createMagnetHolesSketch(component)
    # Extrude
    distance = createDistance(magnetThiccness)
    component.features.extrudeFeatures.addSimple(magnet_holes_profile, distance, CUT)

    # Profile for the edge
    edge_sketch = component.sketches.add(component.xYConstructionPlane)
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

    # Do the sweep
    sweeps = component.features.sweepFeatures
    sweep_input = sweeps.createInput(edge_profile, sweep_path, CUT)
    sweep = sweeps.add(sweep_input)

    # Copy for the whole base
    rectPattern(base_body, slotsWide, slotsDeep, slotDimension)

    # Now the box
    box_path_objects, box_profile = createCurvedRect(component, slotsWide * slotDimension, slotsDeep * slotDimension, baseCornerRadius, nestingDepth)
    distance = createDistance(slotsHigh * slotDimension - nestingDepth)
    base = component.features.extrudeFeatures.addSimple(box_profile, distance, JOIN)

    # Rim
    rim_profile = createRimSketch(component)
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
        if close(mn.y, slotsHigh * slotDimension) and close(mx.y, slotsHigh * slotDimension):
            #print(f'[{mn.x}, {mn.y}, {mn.z}] -> [{mx.x}, {mx.y}, {mx.z}]')
            count += 1
            extrude_face = f.item(n)
    assert count == 1

    # And extrude it
    # FIXME: the + 1 * SCALE is ad hoc (but copied from the original)
    distance = createDistance(-(slotsHigh * slotDimension - (nestingDepth + wallThiccness + 1 * SCALE)))
    component.features.extrudeFeatures.addSimple(extrude_face, distance, CUT)

    # Indent the lower part of the box to leave a rim around the top
    indent_profile = createIndentSketch(component)
    sweep_input = sweeps.createInput(indent_profile, box_path, CUT)
    sweep = sweeps.add(sweep_input)

    # Add the ledge
    ledge_profile = createLedgeSketch(component)
    distance = createDistance(slotsWide * slotDimension - wallThiccness * 4)
    component.features.extrudeFeatures.addSimple(ledge_profile, distance, JOIN)

    # Add the curved scoop
    edges = base_body.edges
    ty = nestingDepth + wallThiccness + 1 * SCALE
    #print(ty)
    fillet_edge = None
    count = 0
    for n in range(edges.count):
        edge = edges.item(n)
        bb = edge.boundingBox
        mx = bb.maxPoint
        mn = bb.minPoint
        # FIXME: where does -8.2354 come from?
        if close(mn.y, ty) and close(mx.y, ty) and close(mn.x, baseCornerRadius) and close(mx.x, slotsWide * slotDimension - baseCornerRadius) and close(mn.z, -(slotsDeep * slotDimension - .1646)):
            #print(f'[{mn.x}, {mn.y}, {mn.z}] -> [{mx.x}, {mx.y}, {mx.z}]')
            fillet_edge = edge
            count += 1
    assert count == 1

    fillet_input = fillets.createInput()
    fillet_radius = createDistance(slotDimension * slotsHigh / 2)
    edges = adsk.core.ObjectCollection.create()
    edges.add(fillet_edge)
    fillet_input.addConstantRadiusEdgeSet(edges, fillet_radius, False)
    fillet_input.isG2 = False
    fillet_input.isRollingBallCorner = True
    fillets.add(fillet_input)


    # Now we're a box. :-)
    base_body.name = "Box"

    # Finally, dividers
    # FIXME: these end up not *quite* the same size
    l = slotsWide * slotDimension - 2 * wallThiccness
    for n in range(dividerCount):
        y = (n + 1) * l / (dividerCount + 1) + wallThiccness / 2
        divider_profile = createDividerSketch(component, y)
        distance = createDistance(wallThiccness)
        divider = component.features.extrudeFeatures.addSimple(divider_profile, distance, JOIN)

        edges = adsk.core.ObjectCollection.create()
        #print(y)
        for n in range(divider.faces.count):
            f = divider.faces.item(n)
            bb = f.boundingBox
            mx = bb.maxPoint
            mn = bb.minPoint
            if (close(mn.x, y) and close(mx.x, y)) or (close(mn.x, y +  wallThiccness) and close(mx.x, y + wallThiccness)):
                #print(f'[{mn.x}, {mn.y}, {mn.z}] -> [{mx.x}, {mx.y}, {mx.z}]')
                for e in range(f.edges.count):
                    edges.add(f.edges.item(e))
        fillet_input = fillets.createInput()
        fillet_radius = createDistance(.6 * SCALE)
        fillet_input.addConstantRadiusEdgeSet(edges, fillet_radius, True)
        fillet_input.isG2 = False
        fillet_input.isRollingBallCorner = True
        fillets.add(fillet_input)

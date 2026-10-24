# Generates probe.paste / probe.ops for BP_JumpProbe.
#   python gen.py <outdir> <vars.log>   (vars.log = output of the addvar edit, for the variable guids)
import sys, os, re
out = sys.argv[1]
G = dict(re.findall(r"added variable (\w+) \([^)]*\) guid=(\w+)", open(sys.argv[2], encoding="utf-8", errors="ignore").read()))
JUMP_HEIGHT = 250.0  # unreal units, about 2.5 blocks (200 measured as 2 blocks)

nodes = []; pos = [0]
def node(name, cls, *props):
    pos[0] += 1
    body = "\n".join("   " + p for p in props)
    nodes.append('Begin Object Class=%s Name="%s"\n%s\n   NodePosX=%d\n   NodePosY=%d\nEnd Object'
                 % (cls, name, body, (pos[0] % 12) * 260, (pos[0] // 12) * 220))
CF = "/Script/BlueprintGraph.K2Node_CallFunction"
def fn(name, parent, member, pure=False, const=False):
    p = []
    if pure: p.append("bIsPureFunc=True")
    if const: p.append("bIsConstFunc=True")
    p.append("FunctionReference=(MemberParent=Class'\"%s\"',MemberName=\"%s\")" % (parent, member))
    node(name, CF, *p)
def selffn(name, member):
    node(name, CF, 'FunctionReference=(MemberName="%s",bSelfContext=True)' % member)
def vget(name, var):
    node(name, "/Script/BlueprintGraph.K2Node_VariableGet", 'VariableReference=(MemberName="%s",MemberGuid=%s,bSelfContext=True)' % (var, G[var]))
def vset(name, var):
    node(name, "/Script/BlueprintGraph.K2Node_VariableSet", 'VariableReference=(MemberName="%s",MemberGuid=%s,bSelfContext=True)' % (var, G[var]))
def xget(name, parent, var, cls="Class"):
    node(name, "/Script/BlueprintGraph.K2Node_VariableGet",
         "VariableReference=(MemberParent=%s'\"%s\"',MemberName=\"%s\")" % (cls, parent, var), "SelfContextInfo=NotSelfContext")
def xset(name, parent, var):
    node(name, "/Script/BlueprintGraph.K2Node_VariableSet",
         "VariableReference=(MemberParent=Class'\"%s\"',MemberName=\"%s\")" % (parent, var), "SelfContextInfo=NotSelfContext")
def mk(name, struct, kind="MakeStruct"):
    node(name, "/Script/BlueprintGraph.K2Node_" + kind, "StructType=ScriptStruct'\"%s\"'" % struct)
def isvalid(name):
    node(name, "/Script/BlueprintGraph.K2Node_MacroInstance",
         "MacroGraphReference=(MacroGraph=EdGraph'\"/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:IsValid\"',GraphBlueprint=Blueprint'\"/Engine/EditorBlueprintResources/StandardMacros.StandardMacros\"',GraphGuid=64422BCD430703FF5CAEA8B79A32AA65)")
def branch(name):
    node(name, "/Script/BlueprintGraph.K2Node_IfThenElse")

GS, KSL, KML, KTL = "/Script/Engine.GameplayStatics", "/Script/Engine.KismetSystemLibrary", "/Script/Engine.KismetMathLibrary", "/Script/Engine.KismetTextLibrary"
CH, ACT, MC, NMC, CMC, INS = ("/Script/Engine.Character", "/Script/Engine.Actor", "/Script/Engine.MovementComponent",
                              "/Script/Engine.NavMovementComponent", "/Script/Engine.CharacterMovementComponent", "/Script/Engine.InputSettings")
ops = []
def L(a, b): ops.append("link %s -> %s" % (a, b))
def S(p, v): ops.append("set %s = %s" % (p, v))
def chain(*refs):
    for a, b in zip(refs, refs[1:]):
        L(a + ".then", b + ".execute")

# --- BeginPlay: debug widget, then move DodgeForward from Space to R
fn("Dly", KSL, "Delay"); S("new:Dly.Duration", "0.5")
fn("GPC", GS, "GetPlayerController", pure=True)
vset("SetPC", "PC"); selffn("EI", "EnableInput"); vget("GetPC1", "PC")
node("CW", "/Script/UMGEditor.K2Node_CreateWidget")
vset("SetDbg", "Dbg"); fn("ATV", "/Script/UMG.UserWidget", "AddToViewport")
fn("GIS", INS, "GetInputSettings", pure=True)
mk("MkOld", "/Script/Engine.InputActionKeyMapping"); mk("MkNew", "/Script/Engine.InputActionKeyMapping")
fn("Rem", INS, "RemoveActionMapping"); fn("Add", INS, "AddActionMapping"); vset("SetRemap", "Remap")
# Quick-chat wheel (QuickActions; LT is assigned at runtime, the ini has Key=None) also on D-pad Left,
# since LT is consumed for jumping below.
mk("MkChat", "/Script/Engine.InputActionKeyMapping"); fn("AddChat", INS, "AddActionMapping")
L("K2Node_Event_0.then", "new:Dly.execute")
chain("new:Dly", "new:SetPC", "new:EI", "new:CW", "new:SetDbg", "new:ATV", "new:Rem", "new:Add", "new:AddChat", "new:SetRemap")
L("new:GIS.ReturnValue", "new:AddChat.self"); L("new:MkChat.InputActionKeyMapping", "new:AddChat.KeyMapping")
S("new:MkChat.ActionName", "QuickActions"); S("new:MkChat.Key", "Gamepad_DPad_Left")
# No rebuild: InputSettings.ForceRebuildKeymaps resets every PlayerInput to the ini defaults, which drops the
# controller bindings the game adds at runtime (only the left stick and our LT worked until a mouse click).
# The edits live on the InputSettings CDO for the whole session and are picked up by the game's own
# rebuilds; the JMP_Menu loader level makes them before the first camp or mission loads.
for n in ("Rem", "Add", "AddChat"):
    S("new:%s.bForceRebuildKeymaps" % n, "false")
L("new:GPC.ReturnValue", "new:SetPC.PC"); L("new:GetPC1.PC", "new:EI.PlayerController")
S("new:CW.Class", "/Game/Mods/Jump/W_JumpDebug.W_JumpDebug_C"); L("new:GetPC1.PC", "new:CW.OwningPlayer")
L("new:CW.ReturnValue", "new:SetDbg.Dbg"); L("new:SetDbg.Output_Get", "new:ATV.self")
L("new:GIS.ReturnValue", "new:Rem.self"); L("new:MkOld.InputActionKeyMapping", "new:Rem.KeyMapping")
L("new:GIS.ReturnValue", "new:Add.self"); L("new:MkNew.InputActionKeyMapping", "new:Add.KeyMapping")
S("new:SetRemap.Remap", "roll Space -> R, chat wheel + D-pad Left")
S("new:MkOld.ActionName", "DodgeForward"); S("new:MkOld.Key", "SpaceBar")
S("new:MkNew.ActionName", "DodgeForward"); S("new:MkNew.Key", "R")

# --- Space (ground only): take-off speed from the game's real gravity for JUMP_HEIGHT,
#     then Jump() if CanJump, else LaunchCharacter with the same speed. Release: StopJumping.
# Consumed: the game re-adds Space -> DodgeForward at runtime (like its pad bindings), so RemoveActionMapping
# alone can't free it, and an unconsumed press rolled instead of jumping. Space no longer interacts either.
node("KSpace", "/Script/BlueprintGraph.K2Node_InputKey", "InputKey=SpaceBar", "bConsumeInput=True")
fn("GPCh", GS, "GetPlayerCharacter", pure=True); vset("SetChar", "Char"); vget("GetChar1", "Char")
xget("GCM1", CH, "CharacterMovement"); fn("OnG1", NMC, "IsMovingOnGround", pure=True, const=True)
branch("BrG"); vset("SetLP0", "LastPath")
fn("GGZ1", MC, "GetGravityZ", pure=True, const=True); fn("Abs1", KML, "Abs", pure=True)
fn("Mul1", KML, "Multiply_FloatFloat", pure=True); fn("Sq1", KML, "Sqrt", pure=True)
xset("SetJZ", CMC, "JumpZVelocity")
fn("Loc1", ACT, "K2_GetActorLocation", pure=True, const=True); fn("BrLoc1", KML, "BreakVector", pure=True)
vset("SetGZ", "GroundZ"); vset("SetPk0", "Peak")
fn("CanJ", CH, "CanJump", pure=True, const=True); branch("Br")
fn("Jmp", CH, "Jump"); vset("SetLP1", "LastPath"); vget("GetJ", "Jumps"); fn("AddJ", KML, "Add_IntInt", pure=True); vset("SetJ", "Jumps")
fn("Lch", CH, "LaunchCharacter"); fn("MkV", KML, "MakeVector", pure=True)
vset("SetLP2", "LastPath"); vget("GetLa", "Launches"); fn("AddLa", KML, "Add_IntInt", pure=True); vset("SetLa", "Launches")
fn("StopJ", CH, "StopJumping"); fn("GPCh3", GS, "GetPlayerCharacter", pure=True)

# Each jump key records its name, then joins the same path. LT is consumed so it no longer opens the
# quick-chat wheel (online only; moved to D-pad Left above). Consuming works on the game's runtime pad
# bindings: consuming RB blocked the forward roll in an earlier probe.
JUMP_KEYS = [("KSpace", None, "Space"), ("KPadLT", "Gamepad_LeftTrigger", "LT")]
for name, key, label in JUMP_KEYS:
    if key:
        node(name, "/Script/BlueprintGraph.K2Node_InputKey", "InputKey=" + key, "bConsumeInput=True")
    vset("SetKey" + name, "LastKey")
    L("new:%s.Pressed" % name, "new:SetKey%s.execute" % name); S("new:SetKey%s.LastKey" % name, label)
    L("new:SetKey%s.then" % name, "new:SetChar.execute")
    L("new:%s.Released" % name, "new:StopJ.execute")
L("new:GPCh.ReturnValue", "new:SetChar.Char")
L("new:GetChar1.Char", "new:GCM1.self"); L("new:GCM1.CharacterMovement", "new:OnG1.self"); L("new:OnG1.ReturnValue", "new:BrG.Condition")
chain("new:SetChar", "new:BrG")
L("new:BrG.else", "new:SetLP0.execute"); S("new:SetLP0.LastPath", "ignored (already in the air)")
L("new:GCM1.CharacterMovement", "new:GGZ1.self"); L("new:GGZ1.ReturnValue", "new:Abs1.A")
L("new:Abs1.ReturnValue", "new:Mul1.A"); S("new:Mul1.B", "%f" % (2 * JUMP_HEIGHT)); L("new:Mul1.ReturnValue", "new:Sq1.A")
L("new:BrG.then", "new:SetJZ.execute"); L("new:GCM1.CharacterMovement", "new:SetJZ.self"); L("new:Sq1.ReturnValue", "new:SetJZ.JumpZVelocity")
L("new:GetChar1.Char", "new:Loc1.self"); L("new:Loc1.ReturnValue", "new:BrLoc1.InVec")
L("new:BrLoc1.Z", "new:SetGZ.GroundZ"); L("new:BrLoc1.Z", "new:SetPk0.Peak")
chain("new:SetJZ", "new:SetGZ", "new:SetPk0", "new:Br")
L("new:GetChar1.Char", "new:CanJ.self"); L("new:CanJ.ReturnValue", "new:Br.Condition")
L("new:Br.then", "new:Jmp.execute"); L("new:GetChar1.Char", "new:Jmp.self")
chain("new:Jmp", "new:SetLP1", "new:SetJ"); S("new:SetLP1.LastPath", "Jump()")
L("new:GetJ.Jumps", "new:AddJ.A"); S("new:AddJ.B", "1"); L("new:AddJ.ReturnValue", "new:SetJ.Jumps")
L("new:Br.else", "new:Lch.execute"); L("new:GetChar1.Char", "new:Lch.self")
L("new:Sq1.ReturnValue", "new:MkV.Z"); L("new:MkV.ReturnValue", "new:Lch.LaunchVelocity"); S("new:Lch.bZOverride", "true")
chain("new:Lch", "new:SetLP2", "new:SetLa"); S("new:SetLP2.LastPath", "LaunchCharacter (CanJump was false)")
L("new:GetLa.Launches", "new:AddLa.A"); S("new:AddLa.B", "1"); L("new:AddLa.ReturnValue", "new:SetLa.Launches")
L("new:GPCh3.ReturnValue", "new:StopJ.self")

# --- Tick: track the peak of the current jump, then the readout
vget("GetDbg", "Dbg"); isvalid("IV")
fn("GPCh2", GS, "GetPlayerCharacter", pure=True)
xget("GCM", CH, "CharacterMovement")
fn("CanJ2", CH, "CanJump", pure=True, const=True)
xget("Nav", NMC, "NavAgentProps"); mk("BrNav", "/Script/Engine.NavAgentProperties", "BreakStruct")
fn("OnG", NMC, "IsMovingOnGround", pure=True, const=True); fn("Fal", NMC, "IsFalling", pure=True, const=True)
xget("MM", CMC, "MovementMode"); fn("MMi", KML, "Conv_ByteToInt", pure=True)
xget("JZ", CMC, "JumpZVelocity"); xget("Grav", CMC, "GravityScale"); fn("GGZ", MC, "GetGravityZ", pure=True, const=True)
fn("Loc", ACT, "K2_GetActorLocation", pure=True, const=True); fn("BrLoc", KML, "BreakVector", pure=True)
fn("Vel", ACT, "GetVelocity", pure=True, const=True); fn("BrVel", KML, "BreakVector", pure=True)
vget("GetPk", "Peak"); fn("MaxPk", KML, "FMax", pure=True); vset("SetPk", "Peak")
vget("GetPk2", "Peak"); vget("GetGZ", "GroundZ"); fn("SubPk", KML, "Subtract_FloatFloat", pure=True)
for n in ("T1", "T2", "T3", "T4"): fn(n, KTL, "Conv_BoolToText", pure=True)
vget("GetLP", "LastPath"); vget("GetLK", "LastKey"); vget("GetJ2", "Jumps"); vget("GetLa2", "Launches"); vget("GetRm", "Remap")
node("Fmt", "/Script/BlueprintGraph.K2Node_FormatText")
xget("DT", "/Game/Mods/Jump/W_JumpDebug.W_JumpDebug_C", "DebugText", "WidgetBlueprintGeneratedClass")
fn("ST", "/Script/UMG.TextBlock", "SetText")
L("K2Node_Event_2.then", "new:SetPk.execute"); L("new:SetPk.then", "new:IV.exec")
L("new:GetPk.Peak", "new:MaxPk.A"); L("new:BrLoc.Z", "new:MaxPk.B"); L("new:MaxPk.ReturnValue", "new:SetPk.Peak")
L("new:GetDbg.Dbg", "new:IV.InputObject")
L("new:IV.Is Valid", "new:ST.execute"); L("new:GetDbg.Dbg", "new:DT.self"); L("new:DT.DebugText", "new:ST.self")
S("new:Fmt.Format", r"JUMP PROBE   Space / LT = jump (target %d high), R = forward roll\nCanJump {CJ}   NavAgent bCanJump {NJ}\nOnGround {G}   Falling {F}   MovementMode {M}\nJumpZVelocity {Z}   GravityZ {GZ}   GravityScale {GS}\nHeight {H}   VelocityZ {VZ}   Last jump peak {PK}\nLast press: {K} -> {L}   Jumps {J}   Launches {LA}\nRemap: {R}" % JUMP_HEIGHT)
L("new:Fmt.Result", "new:ST.InText")
L("new:GPCh2.ReturnValue", "new:GCM.self"); L("new:GPCh2.ReturnValue", "new:CanJ2.self"); L("new:GPCh2.ReturnValue", "new:Loc.self"); L("new:GPCh2.ReturnValue", "new:Vel.self")
L("new:CanJ2.ReturnValue", "new:T1.InBool"); L("new:T1.ReturnValue", "new:Fmt.CJ")
L("new:GCM.CharacterMovement", "new:Nav.self"); L("new:Nav.NavAgentProps", "new:BrNav.NavAgentProperties"); L("new:BrNav.bCanJump", "new:T2.InBool"); L("new:T2.ReturnValue", "new:Fmt.NJ")
L("new:GCM.CharacterMovement", "new:OnG.self"); L("new:OnG.ReturnValue", "new:T3.InBool"); L("new:T3.ReturnValue", "new:Fmt.G")
L("new:GCM.CharacterMovement", "new:Fal.self"); L("new:Fal.ReturnValue", "new:T4.InBool"); L("new:T4.ReturnValue", "new:Fmt.F")
L("new:GCM.CharacterMovement", "new:MM.self"); L("new:MM.MovementMode", "new:MMi.InByte"); L("new:MMi.ReturnValue", "new:Fmt.M")
L("new:GCM.CharacterMovement", "new:JZ.self"); L("new:JZ.JumpZVelocity", "new:Fmt.Z")
L("new:GCM.CharacterMovement", "new:Grav.self"); L("new:Grav.GravityScale", "new:Fmt.GS")
L("new:GCM.CharacterMovement", "new:GGZ.self"); L("new:GGZ.ReturnValue", "new:Fmt.GZ")
L("new:Loc.ReturnValue", "new:BrLoc.InVec"); L("new:BrLoc.Z", "new:Fmt.H")
L("new:Vel.ReturnValue", "new:BrVel.InVec"); L("new:BrVel.Z", "new:Fmt.VZ")
L("new:GetPk2.Peak", "new:SubPk.A"); L("new:GetGZ.GroundZ", "new:SubPk.B"); L("new:SubPk.ReturnValue", "new:Fmt.PK")
L("new:GetLP.LastPath", "new:Fmt.L"); L("new:GetLK.LastKey", "new:Fmt.K");L("new:GetJ2.Jumps", "new:Fmt.J"); L("new:GetLa2.Launches", "new:Fmt.LA"); L("new:GetRm.Remap", "new:Fmt.R")

open(os.path.join(out, "probe.paste"), "w", encoding="utf-8").write("\n".join(nodes) + "\n")
open(os.path.join(out, "probe.ops"), "w", encoding="utf-8").write("\n".join(ops) + "\n")
print(len(nodes), "nodes", len(ops), "ops")

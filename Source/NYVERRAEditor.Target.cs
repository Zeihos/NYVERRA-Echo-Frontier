using UnrealBuildTool;
using System.Collections.Generic;
public class NYVERRAEditorTarget : TargetRules {
 public NYVERRAEditorTarget(TargetInfo Target) : base(Target) {
  Type = TargetType.Editor;
  DefaultBuildSettings = BuildSettingsVersion.V7;
  ExtraModuleNames.Add("NYVERRA");
 }
}

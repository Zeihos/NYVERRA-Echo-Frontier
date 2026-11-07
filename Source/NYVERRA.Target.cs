using UnrealBuildTool;
using System.Collections.Generic;
public class NYVERRATarget : TargetRules {
 public NYVERRATarget(TargetInfo Target) : base(Target) {
  Type = TargetType.Game;
  DefaultBuildSettings = BuildSettingsVersion.V5;
  ExtraModuleNames.Add("NYVERRA");
 }
}

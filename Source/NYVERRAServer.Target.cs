using UnrealBuildTool;
using System.Collections.Generic;
public class NYVERRAServerTarget : TargetRules {
 public NYVERRAServerTarget(TargetInfo Target) : base(Target) {
  Type = TargetType.Server;
  DefaultBuildSettings = BuildSettingsVersion.V5;
  ExtraModuleNames.Add("NYVERRA");
 }
}

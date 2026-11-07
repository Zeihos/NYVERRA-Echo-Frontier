using UnrealBuildTool;
public class NYVERRA : ModuleRules {
 public NYVERRA(ReadOnlyTargetRules Target) : base(Target) {
  PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
  PublicDependencyModuleNames.AddRange(new string[]{"Core","CoreUObject","Engine","InputCore","NetCore","AIModule","NavigationSystem"});
 }
}

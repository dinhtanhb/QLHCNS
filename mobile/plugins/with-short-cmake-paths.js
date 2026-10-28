const { withAppBuildGradle } = require('expo/config-plugins');

// Hash long C++ object paths instead of requiring a Windows-wide registry
// change. Keep this in a config plugin so prebuild remains reproducible.
module.exports = function withShortCmakePaths(config) {
  return withAppBuildGradle(config, (result) => {
    const marker = '// IHRMS: bounded CMake object paths';
    // Replace our previous block when regenerating an existing native folder.
    result.modResults.contents = result.modResults.contents.replace(
      /\n\/\/ IHRMS: bounded CMake object paths\nandroid \{[\s\S]*?\n\}\n/g, '',
    );
    result.modResults.contents += `\n${marker}\nandroid {
    externalNativeBuild {
        cmake { buildStagingDirectory file("\${rootDir}/../.cxx") }
    }
    defaultConfig {
        externalNativeBuild {
            cmake { arguments "-DCMAKE_OBJECT_PATH_MAX=240" }
        }
    }
}\n`;
    // Expo sets react.hermesCommand explicitly, which takes precedence over
    // RN's environment override. Preserve the verified portable compiler on
    // Windows when rebuilding a fresh native project outside the repository.
    result.modResults.contents = result.modResults.contents.replace(
      /\n\/\/ IHRMS: portable Windows Hermes\nreact \{[\s\S]*?\n\}\n/g, '',
    );
    result.modResults.contents += `
// IHRMS: portable Windows Hermes
react {
    def portableHermes = System.getenv("REACT_NATIVE_OVERRIDE_HERMES_DIR")
    if (portableHermes && System.getProperty("os.name").toLowerCase().contains("windows")) {
        hermesCommand = new File(portableHermes, "build/bin/hermesc.exe").absolutePath
    }
}
`;
    return result;
  });
};

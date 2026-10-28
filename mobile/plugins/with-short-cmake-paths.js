const { withAppBuildGradle } = require('expo/config-plugins');

// Hash long C++ object paths instead of requiring a Windows-wide registry
// change. Keep this in a config plugin so prebuild remains reproducible.
module.exports = function withShortCmakePaths(config) {
  return withAppBuildGradle(config, (result) => {
    const marker = '// IHRMS: bounded CMake object paths';
    if (!result.modResults.contents.includes(marker)) {
      result.modResults.contents += `\n${marker}\nandroid {
    defaultConfig {
        externalNativeBuild {
            cmake { arguments "-DCMAKE_OBJECT_PATH_MAX=240" }
        }
    }
}\n`;
    }
    return result;
  });
};

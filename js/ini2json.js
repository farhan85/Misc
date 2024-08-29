/**
 * Converts a string representing the contents of a .ini file into
 * an equivalent Json object. Useful for reading config files.
 */
function convertIniToJson(contents) {
    var currentSection = 'default';
    var jsonObj = {[currentSection]: {}};
    contents.split(/\r?\n/)
        .map(line => line.trim())
        .filter(line => { return !line.startsWith('#') && !line.startsWith(';') })  // Ignore comments
        .filter(line => /\[|=/.test(line))                                          // Must contain '[' or '='
        .forEach(line => {
            if (/^\[/.test(line) ) {
                currentSection = line.replace(/\[|\]/g, '');
                jsonObj[currentSection] = {};                                       // Reading new section
            }
            let kvPair = line.split('=').map(val => val.trim());
            jsonObj[currentSection][kvPair[0]] = kvPair[1];                         // Add key/value to json obj
        });
    return jsonObj;
}

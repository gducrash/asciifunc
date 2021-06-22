function tokenizeCode(code) {
    let commandsList = [
        '$', '+', '=', '%', 
        ':', '!', '.', '@',
        '"', '1', '#', '?',
        '/', '\\', '|', '>', '<'
    ]

    let tokensList = [];
    let currentTokenString = '';

    let context = 'out'; // out = outside of command, in = inside of command, str = inside of a string

    for(let i = 0; i < code.length; i++) {
        let char = code[i];
        let prevChar = code[i-1]
        let nextChar = code[i+1]
        let clearTokenString = false;
        let prevContext = context.toString();

        if(commandsList.includes(char) && context == 'out' && nextChar == '(') {
            tokensList.push({
                key: 'commandName',
                value: char
            });
        } else if(char == '(' && context == 'out' && commandsList.includes(prevChar)) {
            tokensList.push({
                key: 'bracketOpen'
            });
            context = 'in';
        } else if(char == ')' && context == 'in') {
            tokensList.push({
                key: 'bracketClose'
            });
            context = 'out';
            clearTokenString = true;
        } else if(char == ',' && context == 'in') {
            tokensList.push({
                key: 'argumentSeparator'
            });
            clearTokenString = true;
        } else if(char == '"') {
            switch(context) {
                case 'str':
                    context = 'in';
                    tokensList.push({
                        key: 'stringClose'
                    });
                    break;
                case 'in':
                    context = 'str';
                    tokensList.push({
                        key: 'stringOpen'
                    });
                    break;
            }
            clearTokenString = true;
        } else if(context == 'in' || context == 'str') {
            currentTokenString += char;
        }

        if(clearTokenString) {
            if(currentTokenString.trim() == '') {
                currentTokenString = '';
                continue;
            }

            let lastToken = tokensList.pop()
            if(prevContext == 'in') {
                if(parseFloat(currentTokenString) == currentTokenString) {
                    //number
                    tokensList.push({
                        key: 'number',
                        value: parseFloat(currentTokenString)
                    });
                } else if(currentTokenString == 'true' || currentTokenString == 'false') {
                    //bool
                    tokensList.push({
                        key: 'bool',
                        value: currentTokenString == 'true'
                    });
                } else {
                    //identifier
                    tokensList.push({
                        key: 'identifier',
                        value: currentTokenString
                    });
                }
            } else if(prevContext == 'str') {
                tokensList.push({
                    key: 'string',
                    value: currentTokenString
                });
            }

            currentTokenString = '';
            tokensList.push(lastToken);
        }
    }
    return tokensList;
}

/*let code = 'comment $ # () #';
console.log(code);
console.log(tokenizeCode(code));*/
function readCode(code) {
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
        let clearTokenString = false;

        if(commandsList.includes(char) && context == 'out') {
            tokensList.push({
                key: 'commandName',
                value: char
            });
        } else if(char == '(' && context == 'out') {
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
        } else if(context == 'in') {
            
        }
    }
}
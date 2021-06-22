const prompt = require('prompt-sync')();

function tokenizeCode(code) {
    let commandsList = [
        '$', '+', '=', '%', 
        ':', '&', '!', '.', '@',
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
            if(context == 'in' && currentTokenString.trim() == '') {
                currentTokenString = '';
            }
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

function evaluateProgram(tokensList) {
    // convert to a list of commands
    let commands = [];
    let newCommand = {};
    tokensList.forEach(token => {
        if(token.key == 'commandName') {
            newCommand.name = token.value;
        } else if(token.key == 'bracketOpen') {
            newCommand.arguments = [];
        } else if(['number', 'string', 'bool', 'identifier'].includes(token.key)) {
            newCommand.arguments.push({
                type: token.key,
                value: token.value
            });
        } else if(token.key == 'bracketClose') {
            commands.push(newCommand);
            newCommand = {};
        }
    });

    // evaluate commands
    let stack = [{
        layer: 'global',
        variables: [],
        functions: []
    }];
    function stackContainsVar(name) {
        let r = false
        stack.forEach(layer => {
            if(layer.variables[name]) r = true;
        });
        return r;
    }
    function getVarStackLayer(name) {
        let r = -1
        let li = 0;
        stack.forEach(layer => {
            if(layer.variables[name] && r == -1) r = li;
            li++;
        });
        return r;
    }

    let pointer = -1;
    while(pointer < commands.length-1) {
        pointer++;
        let command = commands[pointer];
        switch(command.name) {
            case '$':
                if(!command.arguments[0] || command.arguments[0].type != 'identifier') return;
                let varName = command.arguments[0].value;
                let varType = (
                    command.arguments[1] && command.arguments[1].type == 'identifier'
                    && ['num', 'str', 'bool'].includes(command.arguments[1].value)
                ) ? command.arguments[1].value : 'num';
                let defaultValues = {
                    num: 0,
                    str: '',
                    bool: false
                }
                if(!stack[0].variables[varName]) 
                    stack[0].variables[varName] = {
                        type: varType,
                        value: defaultValues[varType]
                    }
                
                break;
            case '+':
                if(!command.arguments[0] || command.arguments[0].type != 'identifier') return;
                if(!stackContainsVar(command.arguments[0].value)) return;
                
                let targetVar = stack[
                    getVarStackLayer(command.arguments[0].value)
                ].variables[command.arguments[0].value];
                let targetNum = (
                    command.arguments[1] && command.arguments[1].type == 'number'
                ) ? command.arguments[1].value : 0;
                if(
                    command.arguments[1] && command.arguments[1].type == 'identifier' 
                    && stackContainsVar(command.arguments[1].value)
                ) {
                    targetNum = stack[
                        getVarStackLayer(command.arguments[1].value)
                    ].variables[command.arguments[1].value].value;
                }

                if(targetVar.type == 'num') targetVar.value += targetNum;
                break;
            case '=':
                if(!command.arguments[0] || command.arguments[0].type != 'identifier') return;
                if(!stackContainsVar(command.arguments[0].value)) return;
                
                let targetVarEq = stack[
                    getVarStackLayer(command.arguments[0].value)
                ].variables[command.arguments[0].value];
                let targetNumEq = (
                    command.arguments[1] && command.arguments[1].type == 'number'
                ) ? command.arguments[1].value : 0;
                if(
                    command.arguments[1] && command.arguments[1].type == 'identifier' 
                    && stackContainsVar(command.arguments[1].value)
                ) {
                    targetNumEq = stack[
                        getVarStackLayer(command.arguments[1].value)
                    ].variables[command.arguments[1].value].value;
                }
                if(targetVarEq.type == 'num') targetVarEq.value = targetNumEq;
                break;
            case '%':
                if(!command.arguments[0] || command.arguments[0].type != 'identifier') return;
                if(!command.arguments[1] || command.arguments[1].type != 'identifier') return;
                if(!command.arguments[2] || command.arguments[2].type != 'identifier') return;
                if(
                    !stackContainsVar(command.arguments[0].value) ||
                    !stackContainsVar(command.arguments[1].value) ||
                    !stackContainsVar(command.arguments[2].value)
                ) return;
                
                let targetVar1 = stack[
                    getVarStackLayer(command.arguments[0].value)
                ].variables[command.arguments[0].value];
                let targetVar2 = stack[
                    getVarStackLayer(command.arguments[1].value)
                ].variables[command.arguments[1].value];
                let targetVar3 = stack[
                    getVarStackLayer(command.arguments[2].value)
                ].variables[command.arguments[2].value];

                if(targetVar1.type == 'num' && targetVar2.type == 'num' && targetVar3.type == 'num') {
                    if(targetVar1.value > targetVar2.value) targetVar3.value = 1;
                    else if(targetVar1.value < targetVar2.value) targetVar3.value = -1;
                    else targetVar3.value = 0;
                }
                break;
            case ':':
                if(!command.arguments[0] || command.arguments[0].type != 'identifier') return;
                if(!stackContainsVar(command.arguments[0].value)) return;
                
                let targetVarStr = stack[
                    getVarStackLayer(command.arguments[0].value)
                ].variables[command.arguments[0].value];
                let targetNumStr = (
                    command.arguments[1] && command.arguments[1].type == 'string'
                ) ? command.arguments[1].value : '';
                if(
                    command.arguments[1] && command.arguments[1].type == 'identifier' 
                    && stackContainsVar(command.arguments[1].value)
                ) {
                    targetNumStr = stack[
                        getVarStackLayer(command.arguments[1].value)
                    ].variables[command.arguments[1].value].value;
                }
                if(targetVarStr.type == 'str') targetVarStr.value = targetNumStr;
                break;
            case '&':
                if(!command.arguments[0] || command.arguments[0].type != 'identifier') return;
                if(!stackContainsVar(command.arguments[0].value)) return;
                
                let targetVarStr2 = stack[
                    getVarStackLayer(command.arguments[0].value)
                ].variables[command.arguments[0].value];
                let targetNumStr2 = command.arguments[1] ? command.arguments[1].value : '';
                if(
                    command.arguments[1] && command.arguments[1].type == 'identifier' 
                    && stackContainsVar(command.arguments[1].value)
                ) {
                    targetNumStr2 = stack[
                        getVarStackLayer(command.arguments[1].value)
                    ].variables[command.arguments[1].value].value;
                }
                if(targetVarStr2.type == 'str') targetVarStr2.value += targetNumStr2;
                break;
            case '!':
                if(!command.arguments[0] || command.arguments[0].type != 'identifier') return;
                if(!stackContainsVar(command.arguments[0].value)) return;
                
                let targetVarInv = stack[
                    getVarStackLayer(command.arguments[0].value)
                ].variables[command.arguments[0].value];
                if(targetVarInv.type == 'num') targetVarInv.value *= -1;
                else if(targetVarInv.type == 'str') targetVarInv.value = targetVarInv.value.toUpperCase();
                else targetVarInv.value = !targetVarInv.value;
                break;
            case '.':
                if(!command.arguments[0] || command.arguments[0].type != 'identifier') return;
                if(!stackContainsVar(command.arguments[0].value)) return;
                
                let targetVarLwr = stack[
                    getVarStackLayer(command.arguments[0].value)
                ].variables[command.arguments[0].value];
                if(targetVarLwr.type == 'str') targetVarLwr.value = targetVarLwr.value.toLowerCase();
                break;
            case '@':
                if(!command.arguments[0] || command.arguments[0].type != 'identifier') return;
                let num1 = command.arguments[1] ? command.arguments[1].value: 0;
                let num2 = command.arguments[2] ? command.arguments[2].value: 0;
                if(!command.arguments[1] || command.arguments[1].type != 'number') num1 = 0;
                if(!command.arguments[2] || command.arguments[2].type != 'number') num2 = 0;
                
                let targetVarClm = stack[
                    getVarStackLayer(command.arguments[0].value)
                ].variables[command.arguments[0].value];

                if(targetVarClm.type == 'num') {
                    let min = Math.min(num1, num2);
                    let max = Math.max(num1, num2);
                    targetVarClm.value = Math.min(Math.max(targetVarClm.value, min), max);
                } else if(targetVarClm.type == 'str') {
                    targetVarClm.value = targetVarClm.value.slice(num1, num2);
                }
                break;
            case '"':
                if(!command.arguments[0] || command.arguments[0].type != 'identifier') return;
                if(!command.arguments[1] || command.arguments[1].type != 'identifier') return;
                if(
                    !stackContainsVar(command.arguments[0].value) ||
                    !stackContainsVar(command.arguments[1].value)
                ) return;
                
                let targetVarNostr = stack[
                    getVarStackLayer(command.arguments[0].value)
                ].variables[command.arguments[0].value];
                let resultVarStr = stack[
                    getVarStackLayer(command.arguments[1].value)
                ].variables[command.arguments[1].value];

                if(resultVarStr.type == 'str') resultVarStr.value = targetVarNostr.value.toString()
                break;
            case '1':
                if(!command.arguments[0] || command.arguments[0].type != 'identifier') return;
                if(!command.arguments[1] || command.arguments[1].type != 'identifier') return;
                if(
                    !stackContainsVar(command.arguments[0].value) ||
                    !stackContainsVar(command.arguments[1].value)
                ) return;
                
                let targetVarNonum = stack[
                    getVarStackLayer(command.arguments[0].value)
                ].variables[command.arguments[0].value];
                let resultVarNum = stack[
                    getVarStackLayer(command.arguments[1].value)
                ].variables[command.arguments[1].value];

                if(resultVarNum.type == 'num') {
                    resultVarNum.value = targetVarNonum.value * 1;
                    if(resultVarNum.value.toString() == "NaN") resultVarNum.value = 0;
                }
                break;
            case '#':
                let index1;
                if(!command.arguments[0] || command.arguments[0].type != 'number') index1 = commands.length-1;
                else index1 = command.arguments[0].value;
                pointer = index1-1;
                break;
            case '?':
                if(!command.arguments[0] || command.arguments[0].type != 'identifier') return;
                if(!stackContainsVar(command.arguments[0].value)) return;

                let targetVarGt = stack[
                    getVarStackLayer(command.arguments[0].value)
                ].variables[command.arguments[0].value];

                let indexIf;
                if(!command.arguments[1] || command.arguments[1].type != 'number') indexIf = commands.length-1;
                else indexIf = command.arguments[1].value;
                let indexElse;
                if(!command.arguments[2] || command.arguments[2].type != 'number') indexElse = null;
                else indexElse = command.arguments[2].value;
                
                if(targetVarGt.value) pointer = indexIf-1;
                else if(indexElse != null) pointer = indexElse-1;

                break;
            case '<':
                if(!command.arguments[0] || command.arguments[0].type != 'identifier') return;
                if(!stackContainsVar(command.arguments[0].value)) return;
                let targetVarPrnt = stack[
                    getVarStackLayer(command.arguments[0].value)
                ].variables[command.arguments[0].value];
                console.log(targetVarPrnt.value.toString());
                break;
            case '>':
                if(!command.arguments[1] || command.arguments[1].type != 'identifier') return;
                if(!stackContainsVar(command.arguments[1].value)) return;

                let promptType = (
                    command.arguments[0] && command.arguments[0].type == 'identifier'
                    && ['num', 'str', 'bool'].includes(command.arguments[0].value)
                ) ? command.arguments[0].value : 'str';

                let targetVarPrompt = stack[
                    getVarStackLayer(command.arguments[1].value)
                ].variables[command.arguments[1].value];
                let promptRes = prompt('Enter Input > ');
                if(promptType == 'num') promptRes = parseFloat(promptRes);
                else if(promptType == 'bool') promptRes = promptRes == true || promptRes.trim() == 'true';
                
                if(targetVarPrompt.type == promptType) targetVarPrompt.value = promptRes;
                break;
            case '/':
                //todo soon
                break;
            case '\\':
                //todo soon
                break;
            case '|':
                //todo soon
                break;
        }
    }
    return stack[0];
}

let code = 
`truth machine btw this is treated like a comment

declare zero and ones to be accessed later
$(zero, num)
$(one, num)
=(zero, 0)
=(one, 1)

get input
$(input, num)
>(num, input)
@(input, 0, 1)

compare input (will output number)
$(inputCompare, num)
%(input, zero, inputCompare)

convert comparison to bool
?(inputCompare, 10, 12)

print 1 indefinitely
<(one)
#(10)

print 0
<(zero)
`;
console.log(code);
/*console.log(*/evaluateProgram(tokenizeCode(code))//);
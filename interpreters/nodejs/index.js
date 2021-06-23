const prompt = require('prompt-sync')();
const fs = require('fs');

function tokenizeCode(code) {
    // a list of all command names
    let commandsList = [
        '~', '$', '+', '=', '%', 
        ':', '&', '!', '.', '@',
        '"', '1', '#', '?',
        '/', '\\', '|', '>', '<'
    ]

    // data for tokenizing (tokensList contains the result after the process)
    let tokensList = [];
    let currentTokenString = '';
    let context = 'out'; // out = outside of command, in = inside of command, str = inside of a string

    // begin tokenization
    for(let i = 0; i < code.length; i++) {
        let char = code[i];
        let prevChar = code[i-1]
        let nextChar = code[i+1]
        let clearTokenString = false;
        let prevContext = context.toString();

        // command name token
        if(commandsList.includes(char) && context == 'out' && nextChar == '(') {
            tokensList.push({
                key: 'commandName',
                value: char
            });
        // punctuation tokens
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
        // contents of the string or an argument
        } else if(context == 'in' || context == 'str') {
            currentTokenString += char;
            if(context == 'in' && currentTokenString.trim() == '') {
                currentTokenString = '';
            }
        }

        // move currentTokenString to the tokens list and define it's type
        if(clearTokenString) {
            if(currentTokenString.trim() == '') {
                currentTokenString = '';
                continue;
            }

            let lastToken = tokensList.pop()
            if(prevContext == 'in') {
                if(parseFloat(currentTokenString) == currentTokenString) {
                    //number or +index
                    if(currentTokenString.startsWith('+'))
                        tokensList.push({
                            key: 'index',
                            value: currentTokenString
                        });
                    else
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
                // string
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
    // (each command has a name, a list of arguments and a function in which the command is contained)
    let commands = [];
    let newCommand = {};
    let func = '"global"'; // in quotation marks, so that there won't be functions with the same name
    let currentFuncs = [func];
    tokensList.forEach(token => {
        if(token.key == 'commandName') {
            newCommand.name = token.value;
            newCommand.function = currentFuncs[0]; // null - no function
        } else if(token.key == 'bracketOpen') {
            newCommand.arguments = [];
        } else if(['number', 'string', 'bool', 'identifier', 'index'].includes(token.key)) {
            newCommand.arguments.push({
                type: token.key,
                value: token.value
            });
        } else if(token.key == 'bracketClose') {
            commands.push(newCommand);
            if(newCommand.name == '/') {
                if(newCommand.arguments[0].type == 'identifier') currentFuncs.unshift(newCommand.arguments[0].value);
                else currentFuncs.unshift(null);
            } else if(newCommand.name == '\\') {
                currentFuncs.shift();
            }
            newCommand = {};
        }
    });

    // evaluate commands

    // initialize stack
    let stack = [];
    function addStackLayer(name) {
        stack.unshift({
            layer: name,
            variables: [],
            functions: []
        });
    }
    addStackLayer('global');

    // helpful funtions for dealing with variables and functions
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
    function getVar(name) {
        if(typeof name == 'object' && name.value) 
            return stack[
                getVarStackLayer(name.value)
            ].variables[name.value];
        else
            return stack[
                getVarStackLayer(name)
            ].variables[name];
    }

    function stackContainsFunc(name) {
        let r = false
        stack.forEach(layer => {
            if(layer.functions[name]) r = true;
        });
        return r;
    }
    function getFunction(name) {
        let r = null
        stack.forEach(layer => {
            if(layer.functions[name] && r == null) {
                r = layer.functions[name];
            }
        });
        return r;
    }

    // function for performing argument checks
    function performCheck(argument, targetType, special) {
        let fail;
        if(argument && argument.type == targetType) fail = false;
        else fail = true;

        if(!fail && special == 'var') {
            if(!stackContainsVar(argument.value)) fail = true;
        } else if(!fail && special == 'func') {
            if(!stackContainsFunc(argument.value)) fail = true;
        }

        return fail;
    }

    // begin execution
    // pointer - the location of the currently-executing command
    // history - a "stack" of previous pointer and function states (for exiting out of the function)
    // defaultValues - default values for different variable types 
    let pointer = -1;
    let history = [];
    let defaultValues = {
        num: 0,
        str: '',
        bool: false
    }
    while(pointer < commands.length-1) {
        pointer++;
        let command = commands[pointer];
        if(command.function != func) continue;
        switch(command.name) {
            case '$':
                if(performCheck(command.arguments[0], 'identifier')) continue;
                let varName = command.arguments[0].value;
                let varType = (
                    command.arguments[1] && command.arguments[1].type == 'identifier'
                    && ['num', 'str', 'bool'].includes(command.arguments[1].value)
                ) ? command.arguments[1].value : 'num';
                if(!stack[0].variables[varName]) 
                    stack[0].variables[varName] = {
                        type: varType,
                        value: defaultValues[varType]
                    }
                
                break;
            case '+':
                if(performCheck(command.arguments[0], 'identifier', 'var')) continue;
                
                let targetVar = getVar(command.arguments[0])
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
                if(performCheck(command.arguments[0], 'identifier', 'var')) continue;
                
                let targetVarEq = getVar(command.arguments[0])
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
                if(
                    performCheck(command.arguments[0], 'identifier', 'var') ||
                    performCheck(command.arguments[1], 'identifier', 'var') ||
                    performCheck(command.arguments[2], 'identifier', 'var')
                ) continue;
                
                let targetVar1 = getVar(command.arguments[0])
                let targetVar2 = getVar(command.arguments[1])
                let targetVar3 = getVar(command.arguments[2])

                if(targetVar3.type == 'num') {
                    if(targetVar1.value == targetVar2.value) targetVar3.value = 0;
                    else if(targetVar1.value > targetVar2.value) targetVar3.value = 1;
                    else targetVar3.value = -1;
                }
                break;
            case ':':
                if(performCheck(command.arguments[0], 'identifier', 'var')) continue;
                
                let targetVarStr = getVar(command.arguments[0]);
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
                if(performCheck(command.arguments[0], 'identifier', 'var')) continue;
                
                let targetVarStr2 = getVar(command.arguments[0]);
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
                if(performCheck(command.arguments[0], 'identifier', 'var')) continue;
                
                let targetVarInv = getVar(command.arguments[0]);
                if(targetVarInv.type == 'num') targetVarInv.value *= -1;
                else if(targetVarInv.type == 'str') targetVarInv.value = targetVarInv.value.toUpperCase();
                else targetVarInv.value = !targetVarInv.value;
                break;
            case '.':
                if(performCheck(command.arguments[0], 'identifier', 'var')) continue;
                
                let targetVarLwr = getVar(command.arguments[0]);
                if(targetVarLwr.type == 'str') targetVarLwr.value = targetVarLwr.value.toLowerCase();
                break;
            case '@':
                if(performCheck(command.arguments[0], 'identifier', 'var')) continue;
                let num1 = command.arguments[1] ? command.arguments[1].value: 0;
                let num2 = command.arguments[2] ? command.arguments[2].value: 0;
                if(performCheck(command.arguments[1], 'number') && performCheck(command.arguments[1], 'identifier', 'var')) 
                    num1 = 0;
                if(performCheck(command.arguments[2], 'number') && performCheck(command.arguments[2], 'identifier', 'var')) 
                    num2 = 0;
                if(command.arguments[1].type == 'identifier') {
                    num1 = getVar(command.arguments[1]);
                    if(num1.type == 'num') num1 = num1.value
                    else num1 = 0
                }
                if(command.arguments[2].type == 'identifier') {
                    num2 = getVar(command.arguments[2]);
                    if(num2.type == 'num') num2 = num2.value
                    else num2 = 0
                }

                let targetVarClm = getVar(command.arguments[0]);

                if(targetVarClm.type == 'num') {
                    let min = Math.min(num1, num2);
                    let max = Math.max(num1, num2);
                    targetVarClm.value = Math.min(Math.max(targetVarClm.value, min), max);
                } else if(targetVarClm.type == 'str') {
                    targetVarClm.value = targetVarClm.value.slice(num1, num2);
                }
                break;
            case '"':
                if(
                    performCheck(command.arguments[0], 'identifier', 'var') ||
                    performCheck(command.arguments[1], 'identifier', 'var')
                ) continue;
                
                let targetVarNostr = getVar(command.arguments[0]);
                let resultVarStr = getVar(command.arguments[1]);

                if(resultVarStr.type == 'str') resultVarStr.value = targetVarNostr.value.toString()
                break;
            case '1':
                if(
                    performCheck(command.arguments[0], 'identifier', 'var') ||
                    performCheck(command.arguments[1], 'identifier', 'var')
                ) continue;
                
                let targetVarNonum = getVar(command.arguments[0]);
                let resultVarNum = getVar(command.arguments[1]);

                if(resultVarNum.type == 'num') {
                    resultVarNum.value = targetVarNonum.value * 1;
                    if(resultVarNum.value.toString() == "NaN") resultVarNum.value = 0;
                }
                break;
            case '#':
                let index1;
                if(
                    performCheck(command.arguments[0], 'number') && 
                    performCheck(command.arguments[0], 'index')
                ) index1 = commands.length-1;
                else index1 = command.arguments[0].value;
                
                if(index1 < 0 || index1.toString().startsWith('+')) pointer += parseInt(index1)-1
                else pointer = index1-1;
                break;
            case '?':
                if(performCheck(command.arguments[0], 'identifier', 'var')) continue;

                let targetVarGt = getVar(command.arguments[0]);

                let indexIf;
                if(
                    performCheck(command.arguments[1], 'number') && 
                    performCheck(command.arguments[1], 'index')
                ) indexIf = commands.length-1;
                else indexIf = command.arguments[1].value;
                
                let indexElse;
                if(
                    performCheck(command.arguments[2], 'number') && 
                    performCheck(command.arguments[2], 'index')
                ) indexElse = null;
                else indexElse = command.arguments[2].value;
                
                if(targetVarGt.value) {
                    if(indexIf < 0 || indexIf.toString().startsWith('+')) pointer += parseInt(indexIf)-1
                    else pointer = indexIf-1;
                }
                else if(indexElse != null) {
                    if(indexElse < 0 || indexElse.toString().startsWith('+')) pointer += parseInt(indexElse)-1
                    else pointer = indexElse-1;
                }
                break;
            case '<':
                if(performCheck(command.arguments[0], 'identifier', 'var')) continue;
                let targetVarPrnt = getVar(command.arguments[0]);
                console.log(targetVarPrnt.value.toString());
                break;
            case '>':
                if(performCheck(command.arguments[1], 'identifier', 'var')) continue;

                let promptType = (
                    command.arguments[0] && command.arguments[0].type == 'identifier'
                    && ['num', 'str', 'bool'].includes(command.arguments[0].value)
                ) ? command.arguments[0].value : 'str';

                let targetVarPrompt = getVar(command.arguments[1]);
                let promptRes = prompt('Enter Input > ');
                if(promptType == 'num') promptRes = parseFloat(promptRes);
                else if(promptType == 'bool') promptRes = promptRes == true || promptRes.trim() == 'true';
                
                if(targetVarPrompt.type == promptType) targetVarPrompt.value = promptRes;
                break;
            case '/':
                if(performCheck(command.arguments[0], 'identifier')) continue;
                let funcName = command.arguments[0].value;
                // create a function in the current stack layer, if there isnt one already
                if(!stack[0].functions[funcName]) {
                    stack[0].functions[funcName] = {
                        pointer: parseInt(pointer), // parseInt break the reference
                        arguments: command.arguments.slice(1)
                    }
                }
                    
                break;
            case '\\':
                let returnVal = null;
                if(!performCheck(command.arguments[0], 'identifier', 'var')) {
                    returnVal = getVar(command.arguments[0]);
                }

                // remove the last stack layer
                stack.shift();
                // restore the previous state of pointers and func var
                let lastHistoryItem = history.shift();
                pointer = lastHistoryItem.pointer;
                func = lastHistoryItem.func;
                // return value and store in the var
                if(returnVal && lastHistoryItem.retVar) {
                    if(lastHistoryItem.retVar.type == returnVal.type) {
                        lastHistoryItem.retVar.value = returnVal.value;
                    }
                }
                break;
            case '|':
                if(performCheck(command.arguments[0], 'identifier', 'func')) continue;
                
                // get function pointer and arguments
                let targetFunctionData = getFunction(command.arguments[0].value)
                // creater a new stack layer for the function
                addStackLayer(command.arguments[0].value);
                // convert arguments data
                let argi = 0;
                targetFunctionData.arguments.forEach(a => {
                    argi++;
                    let argType = 'num';
                    if(a.value.startsWith('str_')) argType = 'str';
                    else if(a.value.startsWith('bool_')) argType = 'bool'; 
                    let argVal = defaultValues[argType];
                    let curArg = command.arguments[argi]
                    if(!performCheck(curArg, 'identifier', 'var')) {
                        curArg = getVar(curArg);
                    }
                    if(curArg && curArg.type.slice(0,3) == argType.slice(0,3))
                        argVal = curArg.value;

                    stack[0].variables[a.value] = {
                        type: argType,
                        value: argVal
                    }
                });
                let retVar = command.arguments[argi+1];
                if(performCheck(retVar.value, 'identifier', 'var')) {
                    retVar = getVar(retVar);
                } else {
                    retVar = null;
                }
                // add current state to the history
                history.unshift({
                    pointer: pointer,
                    func: func,
                    retVar: retVar
                });
                // change the state to the function's data
                func = command.arguments[0].value;
                pointer = targetFunctionData.pointer;
                break;
        }
    }
    return stack[0];
}

let code;

let arguments = process.argv.slice(2);
let file;
for(let i = 0; i < arguments.length; i++) {
    if(['--file', '-f'].includes(arguments[i])) {
        file = arguments[i+1];
    }
}

if(file) {
    code = fs.readFileSync(file);
    if(code) code = code.toString();
    evaluateProgram(tokenizeCode(code))
}
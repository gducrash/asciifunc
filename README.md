# AsciiFunc
AsciiFunc is an esoteric programming language, that consists of multiple commands, each represented with it's own ascii character. Commands can also have arguments: variables, numbers, bools, strings and pointers. Note that comamnds cannot be stacked, meaning you can't have an argument for a command be another command.

## Commands
| Name | Arguments                                                                        | Description                                                                                                                                                                                                                  | Example                                                                                                                                                 |
|------|----------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| ~    | path (string)                                                                    | Imports another asciifunc file,  which allows for use of it's global  functions and variables.                                                                                                                               | `~("../std-asciifunc.ascf")`                                                                                                                            |
| $    | var name (identifier); var type ("str"/"num"/"bool")                             | Declares a variable in the current  scope. String variables default to "",  number variables default to 0 and  booleans default to false.                                                                                    | ```$(my variable, num) $(variable2, str)```                                                                                                             |
| +    | target var (variable); what to add (number or variable)                          | If the target var is of type number,  adds what's in the second argument  to it. Otherwise, leaves the variable as is. (if the second argument is not a number, also does nothing)                                           | ```+(my variable, 5) +(my variable, variable2)```                                                                                                       |
| =    | target var (variable); target value (number or variable)                         | If the target var is of type number, sets it to what's in the second  argument. Otherwise, leaves it as is. (if the second argument is not a number, also does nothing)                                                      | ```=(variable2, 10) =(my variable, variable2)```                                                                                                        |
| %    | var1 (variable); var2 (variable); var3 (variable);                               | Compares var1 and var2.  If var1 == var2, sets var3 to 0, if var1 > var2, sets var3 to 1,  otherwise, sets var3 to -1.  var3 has to be of a type number, while var1 and var2 can be any type.                                | `%(my variable, variable2, var3)`                                                                                                                       |
| :    | target var (variable); target value (string or variable)                         | If the target var is of type string, sets it to what's in the second  argument. Otherwise, leaves it as is. (if the second argument is not a string, also does nothing)                                                      | `:(variable2, "Hello")`                                                                                                                                 |
| &    | target var (variable); what to add (string or variable)                          | If the target var is of type string, adds what's in the second argument to  the end of it. Otherwise, leaves it as  is. (if the second argument is not a string, also does nothing)                                          | `&(variable2, ", world!")`                                                                                                                              |
| !    | target var (variable)                                                            | If the target var is of type number, multiplies it by -1. If it's of the type string, converts it to upper case. Otherwise, inverts the variable.                                                                            | ```myString is set to "Hi!" !(myString) sets it to "HI!"  myNum is set to 5 !(myNum) sets it to -5  myBool is set to true !(myBool) sets it to false``` |
| .    | target var (variable)                                                            | If the target var is of type string, converts it to lower case. Otherwise, leaves it as is.                                                                                                                                  | ```myString is set to "HI!" .(myString) sets it to "hi!"```                                                                                             |
| @    | target var (variable); arg1 (number or variable); arg2 (number or variable)      | If target var is of type number, clamps it to arg1 and arg2. If target var is of type string, slices it from arg1 to arg2 (similarly to JavaScript's slice  method)                                                          | ```@(myString, 0, -1) @(myNum, -5, 5)```                                                                                                                |
| "    | var1 (variable); var2 (variable)                                                 | Converts var1 to string (similarly to JavaScript's toString method) and stores the result in var2. If var2 is not of type string, does nothing.                                                                              | `"(myNum, myString)`                                                                                                                                    |
| 1    | var1 (variable); var2 (variable)                                                 | Converts var1 to number and stores the  result in var2. If the result is NaN, sets var2 to 0. If var2 is not of type number, does nothing.                                                                                   | `1(my variable, myNum)`                                                                                                                                 |
| #    | index (pointer)                                                                  | Goes to a command #index (aach command  has it's own index, starting from 0  for the first command). index can be a absolute (examples: 5, 6, 12), pr it can be relative to the current  command (examples: -5, +6, +3, -12) | ```#(6) #(+3)```                                                                                                                                        |
| ?    | var (variable); index1 (pointer); index2 (pointer)                               | Checks if var is truthy. If so, goes to command #index1, otherwise goes to command #index2.                                                                                                                                  | `?(myBool, +1, -3)`                                                                                                                                     |
| <    | var (variable)                                                                   | Prints var                                                                                                                                                                                                                   | `<(myString)`                                                                                                                                           |
| >    | type ("num"/"str"/"bool"); var (variable)                                        | Gets user input, then converts it to a specific type and stores it inside var                                                                                                                                                | ```>(str, myString) >(num, myNum) >(bool, myBool)```                                                                                                    |
| /    | function name (identifier); arguments (optional, any amount)                     | Declares and opens a function. Each  function has it's own scope.                                                                                                                                                            | ```/(my function, s)    <(s) \()```                                                                                                                     |
| \    | return value (optional, variable)                                                | Closes the function. Optionally, you can also return a variable                                                                                                                                                              | ```/(helloworld)   $(s, str)   :(s, "Hello, world!") \(s)```                                                                                            |
| \|   | name (function name) arguments (variables or constants) var (optional, variable) | Calls a function with a certain name, providing certain values as arguments. Additionally, you can store the return value for that function inside var                                                                       | ```\|(my function, "Hi!") \|(helloworld, myString)```                                                                                                   |

## Example Code
99 bottles of beer:
```
declare vars
$(bottles, num) $(lyric, str) 

set bottles to 100 - it will subtract -1 before printing
=(bottles, 99) 

begin loop
:(lyric, "") 
&(lyric, bottles) &(lyric, " bottles of beer on the wall, ") 
&(lyric, bottles) &(lyric, " bottles of beer") <(lyric)
:(lyric, "Take one down and pass it around, ") +(bottles, -1) 
&(lyric, bottles) &(lyric, " bottles of beer on the wall") 
<(lyric) :(lyric, "") <(lyric) 
?(bottles, 3)
```

truth machine:
```
truth machine btw this is treated like a comment

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
?(inputCompare, +1, +3)

print 1 indefinitely
<(one)
#(-1)

print 0
<(zero)
```

## Credits
* Python interpreter by [@DexterHill0](https://github.com/DexterHill0) 
* NodeJS interpreter by @GDUcrash (me)

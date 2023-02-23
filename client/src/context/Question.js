
const QuestionStatus = Object.freeze({
    Undefined: Symbol("undefined"), // No question defined
    Loading: Symbol("loading"),     // Question ID defined, but details were not retrieved yet
    Loaded: Symbol("loaded"),       // Question fully loaded, all details are available
});

export { QuestionStatus };

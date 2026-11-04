#ifndef IAConstTerminal_h
#define IAConstTerminal_h

#include "ecf/tree/Terminal.h"
#include "IAPrimitive.h"

class IAConstTerminal : public Tree::Primitives::Terminal, public IAPrimitive
{
public:
	virtual void execute(void* result, Tree::Tree& tree);
	virtual IABounds calculateBounds(Tree::IATree& tree);
};

typedef std::shared_ptr<IAConstTerminal> IAConstTerminalP;

#endif // IAConstTerminal_h

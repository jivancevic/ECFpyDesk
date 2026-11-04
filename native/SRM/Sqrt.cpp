#include "GPSymbRegEvalOp.h"

#include "Sqrt.h"
#include <cmath>

namespace Tree {
namespace Primitives {

Sqrt::Sqrt(void)
{
	nArguments_ = 1;
	name_ = "sqrt";
}


Sqrt::~Sqrt(void)
{	}


void Sqrt::execute(void* result, Tree &tree)
{
	double& arg = *(double*)result;
    getNextArgument(&arg, tree);
	if (arg > 0) {
		arg = sqrt(arg);
	} else {
		arg = 0;
	}
}

}
}
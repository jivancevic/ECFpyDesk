#include "ECF_base.h"
#include "SimpleRandomizer.h"
#include <time.h>
#include <random>


SimpleRandomizer::SimpleRandomizer(uint seed)
{
    if(seed == 0)
		srand((unsigned int) time(NULL));
	else
		srand((unsigned int) seed);
}


int SimpleRandomizer::getRandomInteger(int p, int q) 
{
    return p + (int)( (double)(q-p+1) * (rand() / (RAND_MAX + 1.0)));
}


int SimpleRandomizer::getRandomInteger(uint size) 
{
    return (int)( (double)(size) * (rand() / (RAND_MAX + 1.0)));
}


double SimpleRandomizer::getRandomDouble() 
{
	return rand() / (double(RAND_MAX));
}


void SimpleRandomizer::registerParameters(StateP s) 
{
	s->getRegistry()->registerEntry("randomizer.seed", (voidP) new uint(0), ECF::UINT,
		"randomizer seed, 0 uses time(NULL) (default: 0)");
}


bool SimpleRandomizer::initialize(StateP state)
{
	uint seed = 0;
	if(state->getRegistry()->isModified("randomizer.seed")) {
		voidP sptr = state->getRegistry()->getEntry("randomizer.seed");
		seed = *((int*)sptr.get());
	}

	if(seed != 0)
		srand((unsigned int) seed);
	else {
		// time alone would give processes started in the same second the same run
		std::random_device rd;
#ifdef _MPI
		srand((uint) time(NULL) + state->getCommunicator()->getCommRank() + (uint) rd());
#else
		srand((unsigned int) time(NULL) + (unsigned int) rd());
#endif
	}

	return true;
}
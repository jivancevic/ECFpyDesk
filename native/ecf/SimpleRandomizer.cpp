#include "ECF_base.h"
#include "SimpleRandomizer.h"
#include <time.h>
#include <random>


#ifdef _MSC_VER
// MSVC's RAND_MAX is 32767, which gives doubles only 15 random bits and makes the
// search differ from other systems. rand() stays seeded for ECF code that calls it directly.
static std::mt19937 generator;
static void seedRandom(unsigned int seed) { srand(seed); generator.seed(seed); }
static double nextRandom() { return generator(); }
static const double maxRandom = 4294967295.0;
#else
static void seedRandom(unsigned int seed) { srand(seed); }
static double nextRandom() { return rand(); }
static const double maxRandom = RAND_MAX;
#endif


SimpleRandomizer::SimpleRandomizer(uint seed)
{
    if(seed == 0)
		seedRandom((unsigned int) time(NULL));
	else
		seedRandom((unsigned int) seed);
}


int SimpleRandomizer::getRandomInteger(int p, int q) 
{
    return p + (int)( (double)(q-p+1) * (nextRandom() / (maxRandom + 1.0)));
}


int SimpleRandomizer::getRandomInteger(uint size) 
{
    return (int)( (double)(size) * (nextRandom() / (maxRandom + 1.0)));
}


double SimpleRandomizer::getRandomDouble() 
{
	return nextRandom() / maxRandom;
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
		seedRandom((unsigned int) seed);
	else {
		// time alone would give processes started in the same second the same run
		std::random_device rd;
#ifdef _MPI
		seedRandom((uint) time(NULL) + state->getCommunicator()->getCommRank() + (uint) rd());
#else
		seedRandom((unsigned int) time(NULL) + (unsigned int) rd());
#endif
	}

	return true;
}
#ifndef MOCK_H
#define MOCK_H

#include <cmocka.h>


class mock_tests : public ::testing::Test {
        protected:
                virtual void SetUp() {
                        setup_test(NULL);
                }
                virtual void TearDown() {
                        teardown_test(NULL);
                }

};



#endif // MOCK_H

// g++ -std=c++1y answer.cpp
/*
#include <iostream>
using namespace std;
*/
// ..................................................
// begin LIBRARY
// ..................................................
template<typename T>
class Maybe {
  // 
  //  note: move semantics
  //  (boxed value is never duplicated)
  // 

private:

  bool is_nothing = false;

public:
  T value;

  using boxed_type = T;

  bool isNothing() const { return is_nothing; }

  explicit Maybe () : is_nothing(true) { } // create nothing

  // 
  //  naked values
  // 
  explicit Maybe (T && a) : value(std::move(a)), is_nothing(false) { }

  explicit Maybe (T & a) : value(std::move(a)), is_nothing(false) { }

  // 
  //  boxed values
  // 
  Maybe (Maybe & b) : value(std::move(b.value)), is_nothing(b.is_nothing) { b.is_nothing = true; }

  Maybe (Maybe && b) : value(std::move(b.value)), is_nothing(b.is_nothing) { b.is_nothing = true; }

  Maybe & operator = (Maybe & b) {
    value = std::move(b.value);
    (*this).is_nothing = b.is_nothing;
    b.is_nothing = true;
    return (*this);
  }
}; // class

// ..................................................
template<typename IT, typename F>
auto operator | (Maybe<IT> mi, F f)  // chaining (better with | to avoid parentheses)
{
  // deduce the type of the monad being returned ...
  IT aux;
  using OutMonadType = decltype( f(aux) );
  using OT = typename OutMonadType::boxed_type;

  // just to declare a nothing to return
  Maybe<OT> nothing;

  if (mi.isNothing()) {
    return nothing;
  }

  return f ( mi.value );
} // ()

// ..................................................
template<typename MO>
void showMonad (MO m) {
  // if ( m.isNothing() ) {
  //   cout << " nothing " << endl;
  // } else {
  //   cout << " something : ";
  //   cout << m.value << endl;
  // }
}

// ..................................................
// end LIBRARY
// ..................................................

// ..................................................
int main () {

  auto lengthy = [] (const string & s) -> Maybe<string> { 
    string copyS = s;
    if  (s.length()>8) {
      return Maybe<string> (copyS);
    }
    return Maybe<string> (); // nothing
  };

  auto length = [] (const string & s) -> Maybe<int>{ return Maybe<int> (s.length()); };

  Maybe<string> m1 ("longlonglong");
  Maybe<string> m2 ("short");

  auto res1 = m1 | lengthy  | length;

  auto res2 = m2 | lengthy  | length;

  showMonad (res1);
  showMonad (res2);


} // ()
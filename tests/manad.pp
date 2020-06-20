# 1 "monal.cpp"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "monal.cpp"
# 9 "monal.cpp"
template<typename T>
class Maybe {





private:

  bool is_nothing = false;

public:
  T value;

  using boxed_type = T;

  bool isNothing() const { return is_nothing; }

  explicit Maybe () : is_nothing(true) { }




  explicit Maybe (T && a) : value(std::move(a)), is_nothing(false) { }

  explicit Maybe (T & a) : value(std::move(a)), is_nothing(false) { }




  Maybe (Maybe & b) : value(std::move(b.value)), is_nothing(b.is_nothing) { b.is_nothing = true; }

  Maybe (Maybe && b) : value(std::move(b.value)), is_nothing(b.is_nothing) { b.is_nothing = true; }

  Maybe & operator = (Maybe & b) {
    value = std::move(b.value);
    (*this).is_nothing = b.is_nothing;
    b.is_nothing = true;
    return (*this);
  }
};


template<typename IT, typename F>
auto operator | (Maybe<IT> mi, F f)
{

  IT aux;
  using OutMonadType = decltype( f(aux) );
  using OT = typename OutMonadType::boxed_type;


  Maybe<OT> nothing;

  if (mi.isNothing()) {
    return nothing;
  }

  return f ( mi.value );
}


template<typename MO>
void showMonad (MO m) {






}






int main () {

  auto lengthy = [] (const string & s) -> Maybe<string> {
    string copyS = s;
    if (s.length()>8) {
      return Maybe<string> (copyS);
    }
    return Maybe<string> ();
  };

  auto length = [] (const string & s) -> Maybe<int>{ return Maybe<int> (s.length()); };

  Maybe<string> m1 ("longlonglong");
  Maybe<string> m2 ("short");

  auto res1 = m1 | lengthy | length;

  auto res2 = m2 | lengthy | length;

  showMonad (res1);
  showMonad (res2);


}

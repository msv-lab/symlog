
#include "souffle/CompiledSouffle.h"

namespace functors {
 extern "C" {
}
}

namespace souffle {
static const RamDomain RAM_BIT_SHIFT_MASK = RAM_DOMAIN_SIZE - 1;
struct t_btree_iiii__0_1_2_3__1111__1100 {
static constexpr Relation::arity_type Arity = 4;
using t_tuple = Tuple<RamDomain, 4>;
struct t_comparator_0{
 int operator()(const t_tuple& a, const t_tuple& b) const {
  return (ramBitCast<RamSigned>(a[0]) < ramBitCast<RamSigned>(b[0])) ? -1 : (ramBitCast<RamSigned>(a[0]) > ramBitCast<RamSigned>(b[0])) ? 1 :((ramBitCast<RamSigned>(a[1]) < ramBitCast<RamSigned>(b[1])) ? -1 : (ramBitCast<RamSigned>(a[1]) > ramBitCast<RamSigned>(b[1])) ? 1 :((ramBitCast<RamSigned>(a[2]) < ramBitCast<RamSigned>(b[2])) ? -1 : (ramBitCast<RamSigned>(a[2]) > ramBitCast<RamSigned>(b[2])) ? 1 :((ramBitCast<RamSigned>(a[3]) < ramBitCast<RamSigned>(b[3])) ? -1 : (ramBitCast<RamSigned>(a[3]) > ramBitCast<RamSigned>(b[3])) ? 1 :(0))));
 }
bool less(const t_tuple& a, const t_tuple& b) const {
  return (ramBitCast<RamSigned>(a[0]) < ramBitCast<RamSigned>(b[0]))|| ((ramBitCast<RamSigned>(a[0]) == ramBitCast<RamSigned>(b[0])) && ((ramBitCast<RamSigned>(a[1]) < ramBitCast<RamSigned>(b[1]))|| ((ramBitCast<RamSigned>(a[1]) == ramBitCast<RamSigned>(b[1])) && ((ramBitCast<RamSigned>(a[2]) < ramBitCast<RamSigned>(b[2]))|| ((ramBitCast<RamSigned>(a[2]) == ramBitCast<RamSigned>(b[2])) && ((ramBitCast<RamSigned>(a[3]) < ramBitCast<RamSigned>(b[3]))))))));
 }
bool equal(const t_tuple& a, const t_tuple& b) const {
return (ramBitCast<RamSigned>(a[0]) == ramBitCast<RamSigned>(b[0]))&&(ramBitCast<RamSigned>(a[1]) == ramBitCast<RamSigned>(b[1]))&&(ramBitCast<RamSigned>(a[2]) == ramBitCast<RamSigned>(b[2]))&&(ramBitCast<RamSigned>(a[3]) == ramBitCast<RamSigned>(b[3]));
 }
};
using t_ind_0 = btree_set<t_tuple,t_comparator_0>;
t_ind_0 ind_0;
using iterator = t_ind_0::iterator;
struct context {
t_ind_0::operation_hints hints_0_lower;
t_ind_0::operation_hints hints_0_upper;
};
context createContext() { return context(); }
bool insert(const t_tuple& t) {
context h;
return insert(t, h);
}
bool insert(const t_tuple& t, context& h) {
if (ind_0.insert(t, h.hints_0_lower)) {
return true;
} else return false;
}
bool insert(const RamDomain* ramDomain) {
RamDomain data[4];
std::copy(ramDomain, ramDomain + 4, data);
const t_tuple& tuple = reinterpret_cast<const t_tuple&>(data);
context h;
return insert(tuple, h);
}
bool insert(RamDomain a0,RamDomain a1,RamDomain a2,RamDomain a3) {
RamDomain data[4] = {a0,a1,a2,a3};
return insert(data);
}
bool contains(const t_tuple& t, context& h) const {
return ind_0.contains(t, h.hints_0_lower);
}
bool contains(const t_tuple& t) const {
context h;
return contains(t, h);
}
std::size_t size() const {
return ind_0.size();
}
iterator find(const t_tuple& t, context& h) const {
return ind_0.find(t, h.hints_0_lower);
}
iterator find(const t_tuple& t) const {
context h;
return find(t, h);
}
range<iterator> lowerUpperRange_0000(const t_tuple& /* lower */, const t_tuple& /* upper */, context& /* h */) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<iterator> lowerUpperRange_0000(const t_tuple& /* lower */, const t_tuple& /* upper */) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<t_ind_0::iterator> lowerUpperRange_1111(const t_tuple& lower, const t_tuple& upper, context& h) const {
t_comparator_0 comparator;
int cmp = comparator(lower, upper);
if (cmp == 0) {
    auto pos = ind_0.find(lower, h.hints_0_lower);
    auto fin = ind_0.end();
    if (pos != fin) {fin = pos; ++fin;}
    return make_range(pos, fin);
}
if (cmp > 0) {
    return make_range(ind_0.end(), ind_0.end());
}
return make_range(ind_0.lower_bound(lower, h.hints_0_lower), ind_0.upper_bound(upper, h.hints_0_upper));
}
range<t_ind_0::iterator> lowerUpperRange_1111(const t_tuple& lower, const t_tuple& upper) const {
context h;
return lowerUpperRange_1111(lower,upper,h);
}
range<t_ind_0::iterator> lowerUpperRange_1100(const t_tuple& lower, const t_tuple& upper, context& h) const {
t_comparator_0 comparator;
int cmp = comparator(lower, upper);
if (cmp > 0) {
    return make_range(ind_0.end(), ind_0.end());
}
return make_range(ind_0.lower_bound(lower, h.hints_0_lower), ind_0.upper_bound(upper, h.hints_0_upper));
}
range<t_ind_0::iterator> lowerUpperRange_1100(const t_tuple& lower, const t_tuple& upper) const {
context h;
return lowerUpperRange_1100(lower,upper,h);
}
bool empty() const {
return ind_0.empty();
}
std::vector<range<iterator>> partition() const {
return ind_0.getChunks(400);
}
void purge() {
ind_0.clear();
}
iterator begin() const {
return ind_0.begin();
}
iterator end() const {
return ind_0.end();
}
void printStatistics(std::ostream& o) const {
o << " arity 4 direct b-tree index 0 lex-order [0,1,2,3]\n";
ind_0.printStats(o);
}
};
struct t_btree_iiiii__3_0_1_2_4__11111__00010 {
static constexpr Relation::arity_type Arity = 5;
using t_tuple = Tuple<RamDomain, 5>;
struct t_comparator_0{
 int operator()(const t_tuple& a, const t_tuple& b) const {
  return (ramBitCast<RamSigned>(a[3]) < ramBitCast<RamSigned>(b[3])) ? -1 : (ramBitCast<RamSigned>(a[3]) > ramBitCast<RamSigned>(b[3])) ? 1 :((ramBitCast<RamSigned>(a[0]) < ramBitCast<RamSigned>(b[0])) ? -1 : (ramBitCast<RamSigned>(a[0]) > ramBitCast<RamSigned>(b[0])) ? 1 :((ramBitCast<RamSigned>(a[1]) < ramBitCast<RamSigned>(b[1])) ? -1 : (ramBitCast<RamSigned>(a[1]) > ramBitCast<RamSigned>(b[1])) ? 1 :((ramBitCast<RamSigned>(a[2]) < ramBitCast<RamSigned>(b[2])) ? -1 : (ramBitCast<RamSigned>(a[2]) > ramBitCast<RamSigned>(b[2])) ? 1 :((ramBitCast<RamSigned>(a[4]) < ramBitCast<RamSigned>(b[4])) ? -1 : (ramBitCast<RamSigned>(a[4]) > ramBitCast<RamSigned>(b[4])) ? 1 :(0)))));
 }
bool less(const t_tuple& a, const t_tuple& b) const {
  return (ramBitCast<RamSigned>(a[3]) < ramBitCast<RamSigned>(b[3]))|| ((ramBitCast<RamSigned>(a[3]) == ramBitCast<RamSigned>(b[3])) && ((ramBitCast<RamSigned>(a[0]) < ramBitCast<RamSigned>(b[0]))|| ((ramBitCast<RamSigned>(a[0]) == ramBitCast<RamSigned>(b[0])) && ((ramBitCast<RamSigned>(a[1]) < ramBitCast<RamSigned>(b[1]))|| ((ramBitCast<RamSigned>(a[1]) == ramBitCast<RamSigned>(b[1])) && ((ramBitCast<RamSigned>(a[2]) < ramBitCast<RamSigned>(b[2]))|| ((ramBitCast<RamSigned>(a[2]) == ramBitCast<RamSigned>(b[2])) && ((ramBitCast<RamSigned>(a[4]) < ramBitCast<RamSigned>(b[4]))))))))));
 }
bool equal(const t_tuple& a, const t_tuple& b) const {
return (ramBitCast<RamSigned>(a[3]) == ramBitCast<RamSigned>(b[3]))&&(ramBitCast<RamSigned>(a[0]) == ramBitCast<RamSigned>(b[0]))&&(ramBitCast<RamSigned>(a[1]) == ramBitCast<RamSigned>(b[1]))&&(ramBitCast<RamSigned>(a[2]) == ramBitCast<RamSigned>(b[2]))&&(ramBitCast<RamSigned>(a[4]) == ramBitCast<RamSigned>(b[4]));
 }
};
using t_ind_0 = btree_set<t_tuple,t_comparator_0>;
t_ind_0 ind_0;
using iterator = t_ind_0::iterator;
struct context {
t_ind_0::operation_hints hints_0_lower;
t_ind_0::operation_hints hints_0_upper;
};
context createContext() { return context(); }
bool insert(const t_tuple& t) {
context h;
return insert(t, h);
}
bool insert(const t_tuple& t, context& h) {
if (ind_0.insert(t, h.hints_0_lower)) {
return true;
} else return false;
}
bool insert(const RamDomain* ramDomain) {
RamDomain data[5];
std::copy(ramDomain, ramDomain + 5, data);
const t_tuple& tuple = reinterpret_cast<const t_tuple&>(data);
context h;
return insert(tuple, h);
}
bool insert(RamDomain a0,RamDomain a1,RamDomain a2,RamDomain a3,RamDomain a4) {
RamDomain data[5] = {a0,a1,a2,a3,a4};
return insert(data);
}
bool contains(const t_tuple& t, context& h) const {
return ind_0.contains(t, h.hints_0_lower);
}
bool contains(const t_tuple& t) const {
context h;
return contains(t, h);
}
std::size_t size() const {
return ind_0.size();
}
iterator find(const t_tuple& t, context& h) const {
return ind_0.find(t, h.hints_0_lower);
}
iterator find(const t_tuple& t) const {
context h;
return find(t, h);
}
range<iterator> lowerUpperRange_00000(const t_tuple& /* lower */, const t_tuple& /* upper */, context& /* h */) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<iterator> lowerUpperRange_00000(const t_tuple& /* lower */, const t_tuple& /* upper */) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<t_ind_0::iterator> lowerUpperRange_11111(const t_tuple& lower, const t_tuple& upper, context& h) const {
t_comparator_0 comparator;
int cmp = comparator(lower, upper);
if (cmp == 0) {
    auto pos = ind_0.find(lower, h.hints_0_lower);
    auto fin = ind_0.end();
    if (pos != fin) {fin = pos; ++fin;}
    return make_range(pos, fin);
}
if (cmp > 0) {
    return make_range(ind_0.end(), ind_0.end());
}
return make_range(ind_0.lower_bound(lower, h.hints_0_lower), ind_0.upper_bound(upper, h.hints_0_upper));
}
range<t_ind_0::iterator> lowerUpperRange_11111(const t_tuple& lower, const t_tuple& upper) const {
context h;
return lowerUpperRange_11111(lower,upper,h);
}
range<t_ind_0::iterator> lowerUpperRange_00010(const t_tuple& lower, const t_tuple& upper, context& h) const {
t_comparator_0 comparator;
int cmp = comparator(lower, upper);
if (cmp > 0) {
    return make_range(ind_0.end(), ind_0.end());
}
return make_range(ind_0.lower_bound(lower, h.hints_0_lower), ind_0.upper_bound(upper, h.hints_0_upper));
}
range<t_ind_0::iterator> lowerUpperRange_00010(const t_tuple& lower, const t_tuple& upper) const {
context h;
return lowerUpperRange_00010(lower,upper,h);
}
bool empty() const {
return ind_0.empty();
}
std::vector<range<iterator>> partition() const {
return ind_0.getChunks(400);
}
void purge() {
ind_0.clear();
}
iterator begin() const {
return ind_0.begin();
}
iterator end() const {
return ind_0.end();
}
void printStatistics(std::ostream& o) const {
o << " arity 5 direct b-tree index 0 lex-order [3,0,1,2,4]\n";
ind_0.printStats(o);
}
};
struct t_btree_iiii__1_0_2_3__1111__0100 {
static constexpr Relation::arity_type Arity = 4;
using t_tuple = Tuple<RamDomain, 4>;
struct t_comparator_0{
 int operator()(const t_tuple& a, const t_tuple& b) const {
  return (ramBitCast<RamSigned>(a[1]) < ramBitCast<RamSigned>(b[1])) ? -1 : (ramBitCast<RamSigned>(a[1]) > ramBitCast<RamSigned>(b[1])) ? 1 :((ramBitCast<RamSigned>(a[0]) < ramBitCast<RamSigned>(b[0])) ? -1 : (ramBitCast<RamSigned>(a[0]) > ramBitCast<RamSigned>(b[0])) ? 1 :((ramBitCast<RamSigned>(a[2]) < ramBitCast<RamSigned>(b[2])) ? -1 : (ramBitCast<RamSigned>(a[2]) > ramBitCast<RamSigned>(b[2])) ? 1 :((ramBitCast<RamSigned>(a[3]) < ramBitCast<RamSigned>(b[3])) ? -1 : (ramBitCast<RamSigned>(a[3]) > ramBitCast<RamSigned>(b[3])) ? 1 :(0))));
 }
bool less(const t_tuple& a, const t_tuple& b) const {
  return (ramBitCast<RamSigned>(a[1]) < ramBitCast<RamSigned>(b[1]))|| ((ramBitCast<RamSigned>(a[1]) == ramBitCast<RamSigned>(b[1])) && ((ramBitCast<RamSigned>(a[0]) < ramBitCast<RamSigned>(b[0]))|| ((ramBitCast<RamSigned>(a[0]) == ramBitCast<RamSigned>(b[0])) && ((ramBitCast<RamSigned>(a[2]) < ramBitCast<RamSigned>(b[2]))|| ((ramBitCast<RamSigned>(a[2]) == ramBitCast<RamSigned>(b[2])) && ((ramBitCast<RamSigned>(a[3]) < ramBitCast<RamSigned>(b[3]))))))));
 }
bool equal(const t_tuple& a, const t_tuple& b) const {
return (ramBitCast<RamSigned>(a[1]) == ramBitCast<RamSigned>(b[1]))&&(ramBitCast<RamSigned>(a[0]) == ramBitCast<RamSigned>(b[0]))&&(ramBitCast<RamSigned>(a[2]) == ramBitCast<RamSigned>(b[2]))&&(ramBitCast<RamSigned>(a[3]) == ramBitCast<RamSigned>(b[3]));
 }
};
using t_ind_0 = btree_set<t_tuple,t_comparator_0>;
t_ind_0 ind_0;
using iterator = t_ind_0::iterator;
struct context {
t_ind_0::operation_hints hints_0_lower;
t_ind_0::operation_hints hints_0_upper;
};
context createContext() { return context(); }
bool insert(const t_tuple& t) {
context h;
return insert(t, h);
}
bool insert(const t_tuple& t, context& h) {
if (ind_0.insert(t, h.hints_0_lower)) {
return true;
} else return false;
}
bool insert(const RamDomain* ramDomain) {
RamDomain data[4];
std::copy(ramDomain, ramDomain + 4, data);
const t_tuple& tuple = reinterpret_cast<const t_tuple&>(data);
context h;
return insert(tuple, h);
}
bool insert(RamDomain a0,RamDomain a1,RamDomain a2,RamDomain a3) {
RamDomain data[4] = {a0,a1,a2,a3};
return insert(data);
}
bool contains(const t_tuple& t, context& h) const {
return ind_0.contains(t, h.hints_0_lower);
}
bool contains(const t_tuple& t) const {
context h;
return contains(t, h);
}
std::size_t size() const {
return ind_0.size();
}
iterator find(const t_tuple& t, context& h) const {
return ind_0.find(t, h.hints_0_lower);
}
iterator find(const t_tuple& t) const {
context h;
return find(t, h);
}
range<iterator> lowerUpperRange_0000(const t_tuple& /* lower */, const t_tuple& /* upper */, context& /* h */) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<iterator> lowerUpperRange_0000(const t_tuple& /* lower */, const t_tuple& /* upper */) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<t_ind_0::iterator> lowerUpperRange_1111(const t_tuple& lower, const t_tuple& upper, context& h) const {
t_comparator_0 comparator;
int cmp = comparator(lower, upper);
if (cmp == 0) {
    auto pos = ind_0.find(lower, h.hints_0_lower);
    auto fin = ind_0.end();
    if (pos != fin) {fin = pos; ++fin;}
    return make_range(pos, fin);
}
if (cmp > 0) {
    return make_range(ind_0.end(), ind_0.end());
}
return make_range(ind_0.lower_bound(lower, h.hints_0_lower), ind_0.upper_bound(upper, h.hints_0_upper));
}
range<t_ind_0::iterator> lowerUpperRange_1111(const t_tuple& lower, const t_tuple& upper) const {
context h;
return lowerUpperRange_1111(lower,upper,h);
}
range<t_ind_0::iterator> lowerUpperRange_0100(const t_tuple& lower, const t_tuple& upper, context& h) const {
t_comparator_0 comparator;
int cmp = comparator(lower, upper);
if (cmp > 0) {
    return make_range(ind_0.end(), ind_0.end());
}
return make_range(ind_0.lower_bound(lower, h.hints_0_lower), ind_0.upper_bound(upper, h.hints_0_upper));
}
range<t_ind_0::iterator> lowerUpperRange_0100(const t_tuple& lower, const t_tuple& upper) const {
context h;
return lowerUpperRange_0100(lower,upper,h);
}
bool empty() const {
return ind_0.empty();
}
std::vector<range<iterator>> partition() const {
return ind_0.getChunks(400);
}
void purge() {
ind_0.clear();
}
iterator begin() const {
return ind_0.begin();
}
iterator end() const {
return ind_0.end();
}
void printStatistics(std::ostream& o) const {
o << " arity 4 direct b-tree index 0 lex-order [1,0,2,3]\n";
ind_0.printStats(o);
}
};
struct t_btree_i__0__1 {
static constexpr Relation::arity_type Arity = 1;
using t_tuple = Tuple<RamDomain, 1>;
struct t_comparator_0{
 int operator()(const t_tuple& a, const t_tuple& b) const {
  return (ramBitCast<RamSigned>(a[0]) < ramBitCast<RamSigned>(b[0])) ? -1 : (ramBitCast<RamSigned>(a[0]) > ramBitCast<RamSigned>(b[0])) ? 1 :(0);
 }
bool less(const t_tuple& a, const t_tuple& b) const {
  return (ramBitCast<RamSigned>(a[0]) < ramBitCast<RamSigned>(b[0]));
 }
bool equal(const t_tuple& a, const t_tuple& b) const {
return (ramBitCast<RamSigned>(a[0]) == ramBitCast<RamSigned>(b[0]));
 }
};
using t_ind_0 = btree_set<t_tuple,t_comparator_0>;
t_ind_0 ind_0;
using iterator = t_ind_0::iterator;
struct context {
t_ind_0::operation_hints hints_0_lower;
t_ind_0::operation_hints hints_0_upper;
};
context createContext() { return context(); }
bool insert(const t_tuple& t) {
context h;
return insert(t, h);
}
bool insert(const t_tuple& t, context& h) {
if (ind_0.insert(t, h.hints_0_lower)) {
return true;
} else return false;
}
bool insert(const RamDomain* ramDomain) {
RamDomain data[1];
std::copy(ramDomain, ramDomain + 1, data);
const t_tuple& tuple = reinterpret_cast<const t_tuple&>(data);
context h;
return insert(tuple, h);
}
bool insert(RamDomain a0) {
RamDomain data[1] = {a0};
return insert(data);
}
bool contains(const t_tuple& t, context& h) const {
return ind_0.contains(t, h.hints_0_lower);
}
bool contains(const t_tuple& t) const {
context h;
return contains(t, h);
}
std::size_t size() const {
return ind_0.size();
}
iterator find(const t_tuple& t, context& h) const {
return ind_0.find(t, h.hints_0_lower);
}
iterator find(const t_tuple& t) const {
context h;
return find(t, h);
}
range<iterator> lowerUpperRange_0(const t_tuple& /* lower */, const t_tuple& /* upper */, context& /* h */) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<iterator> lowerUpperRange_0(const t_tuple& /* lower */, const t_tuple& /* upper */) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<t_ind_0::iterator> lowerUpperRange_1(const t_tuple& lower, const t_tuple& upper, context& h) const {
t_comparator_0 comparator;
int cmp = comparator(lower, upper);
if (cmp == 0) {
    auto pos = ind_0.find(lower, h.hints_0_lower);
    auto fin = ind_0.end();
    if (pos != fin) {fin = pos; ++fin;}
    return make_range(pos, fin);
}
if (cmp > 0) {
    return make_range(ind_0.end(), ind_0.end());
}
return make_range(ind_0.lower_bound(lower, h.hints_0_lower), ind_0.upper_bound(upper, h.hints_0_upper));
}
range<t_ind_0::iterator> lowerUpperRange_1(const t_tuple& lower, const t_tuple& upper) const {
context h;
return lowerUpperRange_1(lower,upper,h);
}
bool empty() const {
return ind_0.empty();
}
std::vector<range<iterator>> partition() const {
return ind_0.getChunks(400);
}
void purge() {
ind_0.clear();
}
iterator begin() const {
return ind_0.begin();
}
iterator end() const {
return ind_0.end();
}
void printStatistics(std::ostream& o) const {
o << " arity 1 direct b-tree index 0 lex-order [0]\n";
ind_0.printStats(o);
}
};
struct t_btree_iii__0_1_2__111 {
static constexpr Relation::arity_type Arity = 3;
using t_tuple = Tuple<RamDomain, 3>;
struct t_comparator_0{
 int operator()(const t_tuple& a, const t_tuple& b) const {
  return (ramBitCast<RamSigned>(a[0]) < ramBitCast<RamSigned>(b[0])) ? -1 : (ramBitCast<RamSigned>(a[0]) > ramBitCast<RamSigned>(b[0])) ? 1 :((ramBitCast<RamSigned>(a[1]) < ramBitCast<RamSigned>(b[1])) ? -1 : (ramBitCast<RamSigned>(a[1]) > ramBitCast<RamSigned>(b[1])) ? 1 :((ramBitCast<RamSigned>(a[2]) < ramBitCast<RamSigned>(b[2])) ? -1 : (ramBitCast<RamSigned>(a[2]) > ramBitCast<RamSigned>(b[2])) ? 1 :(0)));
 }
bool less(const t_tuple& a, const t_tuple& b) const {
  return (ramBitCast<RamSigned>(a[0]) < ramBitCast<RamSigned>(b[0]))|| ((ramBitCast<RamSigned>(a[0]) == ramBitCast<RamSigned>(b[0])) && ((ramBitCast<RamSigned>(a[1]) < ramBitCast<RamSigned>(b[1]))|| ((ramBitCast<RamSigned>(a[1]) == ramBitCast<RamSigned>(b[1])) && ((ramBitCast<RamSigned>(a[2]) < ramBitCast<RamSigned>(b[2]))))));
 }
bool equal(const t_tuple& a, const t_tuple& b) const {
return (ramBitCast<RamSigned>(a[0]) == ramBitCast<RamSigned>(b[0]))&&(ramBitCast<RamSigned>(a[1]) == ramBitCast<RamSigned>(b[1]))&&(ramBitCast<RamSigned>(a[2]) == ramBitCast<RamSigned>(b[2]));
 }
};
using t_ind_0 = btree_set<t_tuple,t_comparator_0>;
t_ind_0 ind_0;
using iterator = t_ind_0::iterator;
struct context {
t_ind_0::operation_hints hints_0_lower;
t_ind_0::operation_hints hints_0_upper;
};
context createContext() { return context(); }
bool insert(const t_tuple& t) {
context h;
return insert(t, h);
}
bool insert(const t_tuple& t, context& h) {
if (ind_0.insert(t, h.hints_0_lower)) {
return true;
} else return false;
}
bool insert(const RamDomain* ramDomain) {
RamDomain data[3];
std::copy(ramDomain, ramDomain + 3, data);
const t_tuple& tuple = reinterpret_cast<const t_tuple&>(data);
context h;
return insert(tuple, h);
}
bool insert(RamDomain a0,RamDomain a1,RamDomain a2) {
RamDomain data[3] = {a0,a1,a2};
return insert(data);
}
bool contains(const t_tuple& t, context& h) const {
return ind_0.contains(t, h.hints_0_lower);
}
bool contains(const t_tuple& t) const {
context h;
return contains(t, h);
}
std::size_t size() const {
return ind_0.size();
}
iterator find(const t_tuple& t, context& h) const {
return ind_0.find(t, h.hints_0_lower);
}
iterator find(const t_tuple& t) const {
context h;
return find(t, h);
}
range<iterator> lowerUpperRange_000(const t_tuple& /* lower */, const t_tuple& /* upper */, context& /* h */) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<iterator> lowerUpperRange_000(const t_tuple& /* lower */, const t_tuple& /* upper */) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<t_ind_0::iterator> lowerUpperRange_111(const t_tuple& lower, const t_tuple& upper, context& h) const {
t_comparator_0 comparator;
int cmp = comparator(lower, upper);
if (cmp == 0) {
    auto pos = ind_0.find(lower, h.hints_0_lower);
    auto fin = ind_0.end();
    if (pos != fin) {fin = pos; ++fin;}
    return make_range(pos, fin);
}
if (cmp > 0) {
    return make_range(ind_0.end(), ind_0.end());
}
return make_range(ind_0.lower_bound(lower, h.hints_0_lower), ind_0.upper_bound(upper, h.hints_0_upper));
}
range<t_ind_0::iterator> lowerUpperRange_111(const t_tuple& lower, const t_tuple& upper) const {
context h;
return lowerUpperRange_111(lower,upper,h);
}
bool empty() const {
return ind_0.empty();
}
std::vector<range<iterator>> partition() const {
return ind_0.getChunks(400);
}
void purge() {
ind_0.clear();
}
iterator begin() const {
return ind_0.begin();
}
iterator end() const {
return ind_0.end();
}
void printStatistics(std::ostream& o) const {
o << " arity 3 direct b-tree index 0 lex-order [0,1,2]\n";
ind_0.printStats(o);
}
};
struct t_btree_iiiii__0_1_2_3_4__11111 {
static constexpr Relation::arity_type Arity = 5;
using t_tuple = Tuple<RamDomain, 5>;
struct t_comparator_0{
 int operator()(const t_tuple& a, const t_tuple& b) const {
  return (ramBitCast<RamSigned>(a[0]) < ramBitCast<RamSigned>(b[0])) ? -1 : (ramBitCast<RamSigned>(a[0]) > ramBitCast<RamSigned>(b[0])) ? 1 :((ramBitCast<RamSigned>(a[1]) < ramBitCast<RamSigned>(b[1])) ? -1 : (ramBitCast<RamSigned>(a[1]) > ramBitCast<RamSigned>(b[1])) ? 1 :((ramBitCast<RamSigned>(a[2]) < ramBitCast<RamSigned>(b[2])) ? -1 : (ramBitCast<RamSigned>(a[2]) > ramBitCast<RamSigned>(b[2])) ? 1 :((ramBitCast<RamSigned>(a[3]) < ramBitCast<RamSigned>(b[3])) ? -1 : (ramBitCast<RamSigned>(a[3]) > ramBitCast<RamSigned>(b[3])) ? 1 :((ramBitCast<RamSigned>(a[4]) < ramBitCast<RamSigned>(b[4])) ? -1 : (ramBitCast<RamSigned>(a[4]) > ramBitCast<RamSigned>(b[4])) ? 1 :(0)))));
 }
bool less(const t_tuple& a, const t_tuple& b) const {
  return (ramBitCast<RamSigned>(a[0]) < ramBitCast<RamSigned>(b[0]))|| ((ramBitCast<RamSigned>(a[0]) == ramBitCast<RamSigned>(b[0])) && ((ramBitCast<RamSigned>(a[1]) < ramBitCast<RamSigned>(b[1]))|| ((ramBitCast<RamSigned>(a[1]) == ramBitCast<RamSigned>(b[1])) && ((ramBitCast<RamSigned>(a[2]) < ramBitCast<RamSigned>(b[2]))|| ((ramBitCast<RamSigned>(a[2]) == ramBitCast<RamSigned>(b[2])) && ((ramBitCast<RamSigned>(a[3]) < ramBitCast<RamSigned>(b[3]))|| ((ramBitCast<RamSigned>(a[3]) == ramBitCast<RamSigned>(b[3])) && ((ramBitCast<RamSigned>(a[4]) < ramBitCast<RamSigned>(b[4]))))))))));
 }
bool equal(const t_tuple& a, const t_tuple& b) const {
return (ramBitCast<RamSigned>(a[0]) == ramBitCast<RamSigned>(b[0]))&&(ramBitCast<RamSigned>(a[1]) == ramBitCast<RamSigned>(b[1]))&&(ramBitCast<RamSigned>(a[2]) == ramBitCast<RamSigned>(b[2]))&&(ramBitCast<RamSigned>(a[3]) == ramBitCast<RamSigned>(b[3]))&&(ramBitCast<RamSigned>(a[4]) == ramBitCast<RamSigned>(b[4]));
 }
};
using t_ind_0 = btree_set<t_tuple,t_comparator_0>;
t_ind_0 ind_0;
using iterator = t_ind_0::iterator;
struct context {
t_ind_0::operation_hints hints_0_lower;
t_ind_0::operation_hints hints_0_upper;
};
context createContext() { return context(); }
bool insert(const t_tuple& t) {
context h;
return insert(t, h);
}
bool insert(const t_tuple& t, context& h) {
if (ind_0.insert(t, h.hints_0_lower)) {
return true;
} else return false;
}
bool insert(const RamDomain* ramDomain) {
RamDomain data[5];
std::copy(ramDomain, ramDomain + 5, data);
const t_tuple& tuple = reinterpret_cast<const t_tuple&>(data);
context h;
return insert(tuple, h);
}
bool insert(RamDomain a0,RamDomain a1,RamDomain a2,RamDomain a3,RamDomain a4) {
RamDomain data[5] = {a0,a1,a2,a3,a4};
return insert(data);
}
bool contains(const t_tuple& t, context& h) const {
return ind_0.contains(t, h.hints_0_lower);
}
bool contains(const t_tuple& t) const {
context h;
return contains(t, h);
}
std::size_t size() const {
return ind_0.size();
}
iterator find(const t_tuple& t, context& h) const {
return ind_0.find(t, h.hints_0_lower);
}
iterator find(const t_tuple& t) const {
context h;
return find(t, h);
}
range<iterator> lowerUpperRange_00000(const t_tuple& /* lower */, const t_tuple& /* upper */, context& /* h */) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<iterator> lowerUpperRange_00000(const t_tuple& /* lower */, const t_tuple& /* upper */) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<t_ind_0::iterator> lowerUpperRange_11111(const t_tuple& lower, const t_tuple& upper, context& h) const {
t_comparator_0 comparator;
int cmp = comparator(lower, upper);
if (cmp == 0) {
    auto pos = ind_0.find(lower, h.hints_0_lower);
    auto fin = ind_0.end();
    if (pos != fin) {fin = pos; ++fin;}
    return make_range(pos, fin);
}
if (cmp > 0) {
    return make_range(ind_0.end(), ind_0.end());
}
return make_range(ind_0.lower_bound(lower, h.hints_0_lower), ind_0.upper_bound(upper, h.hints_0_upper));
}
range<t_ind_0::iterator> lowerUpperRange_11111(const t_tuple& lower, const t_tuple& upper) const {
context h;
return lowerUpperRange_11111(lower,upper,h);
}
bool empty() const {
return ind_0.empty();
}
std::vector<range<iterator>> partition() const {
return ind_0.getChunks(400);
}
void purge() {
ind_0.clear();
}
iterator begin() const {
return ind_0.begin();
}
iterator end() const {
return ind_0.end();
}
void printStatistics(std::ostream& o) const {
o << " arity 5 direct b-tree index 0 lex-order [0,1,2,3,4]\n";
ind_0.printStats(o);
}
};

class Sf_original : public SouffleProgram {
private:
static inline std::string substr_wrapper(const std::string& str, std::size_t idx, std::size_t len) {
   std::string result; 
   try { result = str.substr(idx,len); } catch(...) { 
     std::cerr << "warning: wrong index position provided by substr(\"";
     std::cerr << str << "\"," << (int32_t)idx << "," << (int32_t)len << ") functor.\n";
   } return result;
}
public:
// -- initialize symbol table --
SymbolTableImpl symTable{
	R"_(<ArrayNullLoad: void <init>()>)_",
	R"_(1)_",
	R"_(-1)_",
	R"_(ArrayNullLoad.java)_",
	R"_(2)_",
	R"_(3)_",
	R"_(<ArrayNullLoad: void main(java.lang.String[])>)_",
	R"_(4)_",
	R"_(5)_",
	R"_(<ArrayNullLoad: void main(java.lang.String[])>/assign/instruction3)_",
	R"_(<ArrayNullLoad: void main(java.lang.String[])>/i#_4)_",
	R"_(<ArrayNullLoad: void main(java.lang.String[])>/array#_3)_",
	R"_(<<unique-hcontext>>)_",
	R"_(<<main method array>>)_",
	R"_(<ArrayNullLoad: void main(java.lang.String[])>/@parameter0)_",
	R"_(<ArrayNullLoad: void main(java.lang.String[])>/args#_0)_",
	R"_(<<null pseudo heap>>)_",
	R"_(Load Array Index)_",
};// -- initialize record table --
SpecializedRecordTable<0> recordTable{};
// -- Table: InstructionLine
Own<t_btree_iiii__0_1_2_3__1111__1100> rel_1_InstructionLine = mk<t_btree_iiii__0_1_2_3__1111__1100>();
souffle::RelationWrapper<t_btree_iiii__0_1_2_3__1111__1100> wrapper_rel_1_InstructionLine;
// -- Table: LoadArrayIndex
Own<t_btree_iiiii__3_0_1_2_4__11111__00010> rel_2_LoadArrayIndex = mk<t_btree_iiiii__3_0_1_2_4__11111__00010>();
souffle::RelationWrapper<t_btree_iiiii__3_0_1_2_4__11111__00010> wrapper_rel_2_LoadArrayIndex;
// -- Table: VarPointsTo
Own<t_btree_iiii__1_0_2_3__1111__0100> rel_3_VarPointsTo = mk<t_btree_iiii__1_0_2_3__1111__0100>();
souffle::RelationWrapper<t_btree_iiii__1_0_2_3__1111__0100> wrapper_rel_3_VarPointsTo;
// -- Table: VarPointsToNull
Own<t_btree_i__0__1> rel_4_VarPointsToNull = mk<t_btree_i__0__1>();
souffle::RelationWrapper<t_btree_i__0__1> wrapper_rel_4_VarPointsToNull;
// -- Table: NullAt
Own<t_btree_iii__0_1_2__111> rel_5_NullAt = mk<t_btree_iii__0_1_2__111>();
souffle::RelationWrapper<t_btree_iii__0_1_2__111> wrapper_rel_5_NullAt;
// -- Table: Reachable
Own<t_btree_i__0__1> rel_6_Reachable = mk<t_btree_i__0__1>();
souffle::RelationWrapper<t_btree_i__0__1> wrapper_rel_6_Reachable;
// -- Table: ReachableNullAt
Own<t_btree_iii__0_1_2__111> rel_7_ReachableNullAt = mk<t_btree_iii__0_1_2__111>();
souffle::RelationWrapper<t_btree_iii__0_1_2__111> wrapper_rel_7_ReachableNullAt;
// -- Table: ReachableNullAtLine
Own<t_btree_iiiii__0_1_2_3_4__11111> rel_8_ReachableNullAtLine = mk<t_btree_iiiii__0_1_2_3_4__11111>();
souffle::RelationWrapper<t_btree_iiiii__0_1_2_3_4__11111> wrapper_rel_8_ReachableNullAtLine;
public:
Sf_original()
: wrapper_rel_1_InstructionLine(0, *rel_1_InstructionLine, *this, "InstructionLine", std::array<const char *,4>{{"s:symbol","s:symbol","s:symbol","s:symbol"}}, std::array<const char *,4>{{"v0","v1","v2","v3"}}, 0)
, wrapper_rel_2_LoadArrayIndex(1, *rel_2_LoadArrayIndex, *this, "LoadArrayIndex", std::array<const char *,5>{{"s:symbol","s:symbol","s:symbol","s:symbol","s:symbol"}}, std::array<const char *,5>{{"v0","v1","v2","v3","v4"}}, 0)
, wrapper_rel_3_VarPointsTo(2, *rel_3_VarPointsTo, *this, "VarPointsTo", std::array<const char *,4>{{"s:symbol","s:symbol","s:symbol","s:symbol"}}, std::array<const char *,4>{{"v0","v1","v2","v3"}}, 0)
, wrapper_rel_4_VarPointsToNull(3, *rel_4_VarPointsToNull, *this, "VarPointsToNull", std::array<const char *,1>{{"s:symbol"}}, std::array<const char *,1>{{"v0"}}, 0)
, wrapper_rel_5_NullAt(4, *rel_5_NullAt, *this, "NullAt", std::array<const char *,3>{{"s:symbol","s:symbol","s:symbol"}}, std::array<const char *,3>{{"v0","v1","v2"}}, 0)
, wrapper_rel_6_Reachable(5, *rel_6_Reachable, *this, "Reachable", std::array<const char *,1>{{"s:symbol"}}, std::array<const char *,1>{{"v0"}}, 0)
, wrapper_rel_7_ReachableNullAt(6, *rel_7_ReachableNullAt, *this, "ReachableNullAt", std::array<const char *,3>{{"s:symbol","s:symbol","s:symbol"}}, std::array<const char *,3>{{"v0","v1","v2"}}, 0)
, wrapper_rel_8_ReachableNullAtLine(7, *rel_8_ReachableNullAtLine, *this, "ReachableNullAtLine", std::array<const char *,5>{{"s:symbol","s:symbol","s:symbol","s:symbol","s:symbol"}}, std::array<const char *,5>{{"v0","v1","v2","v3","v4"}}, 0)
{
addRelation("InstructionLine", wrapper_rel_1_InstructionLine, false, false);
addRelation("LoadArrayIndex", wrapper_rel_2_LoadArrayIndex, false, false);
addRelation("VarPointsTo", wrapper_rel_3_VarPointsTo, false, false);
addRelation("VarPointsToNull", wrapper_rel_4_VarPointsToNull, false, false);
addRelation("NullAt", wrapper_rel_5_NullAt, false, false);
addRelation("Reachable", wrapper_rel_6_Reachable, false, false);
addRelation("ReachableNullAt", wrapper_rel_7_ReachableNullAt, false, false);
addRelation("ReachableNullAtLine", wrapper_rel_8_ReachableNullAtLine, false, true);
}
~Sf_original() {
}

private:
std::string             inputDirectory;
std::string             outputDirectory;
SignalHandler*          signalHandler {SignalHandler::instance()};
std::atomic<RamDomain>  ctr {};
std::atomic<std::size_t>     iter {};

void runFunction(std::string  inputDirectoryArg,
                 std::string  outputDirectoryArg,
                 bool         performIOArg,
                 bool         pruneImdtRelsArg) {
    this->inputDirectory  = std::move(inputDirectoryArg);
    this->outputDirectory = std::move(outputDirectoryArg);
    this->performIO       = performIOArg;
    this->pruneImdtRels   = pruneImdtRelsArg; 

    // set default threads (in embedded mode)
    // if this is not set, and omp is used, the default omp setting of number of cores is used.
#if defined(_OPENMP)
    if (0 < getNumThreads()) { omp_set_num_threads(static_cast<int>(getNumThreads())); }
#endif

    signalHandler->set();
// -- query evaluation --
{
 std::vector<RamDomain> args, ret;
subroutine_0(args, ret);
}
{
 std::vector<RamDomain> args, ret;
subroutine_1(args, ret);
}
{
 std::vector<RamDomain> args, ret;
subroutine_2(args, ret);
}
{
 std::vector<RamDomain> args, ret;
subroutine_3(args, ret);
}
{
 std::vector<RamDomain> args, ret;
subroutine_4(args, ret);
}
{
 std::vector<RamDomain> args, ret;
subroutine_5(args, ret);
}
{
 std::vector<RamDomain> args, ret;
subroutine_6(args, ret);
}
{
 std::vector<RamDomain> args, ret;
subroutine_7(args, ret);
}

// -- relation hint statistics --
signalHandler->reset();
}
public:
void run() override { runFunction("", "", false, false); }
public:
void runAll(std::string inputDirectoryArg = "", std::string outputDirectoryArg = "", bool performIOArg=true, bool pruneImdtRelsArg=true) override { runFunction(inputDirectoryArg, outputDirectoryArg, performIOArg, pruneImdtRelsArg);
}
public:
void printAll(std::string outputDirectoryArg = "") override {
try {std::map<std::string, std::string> directiveMap({{"IO","file"},{"attributeNames","v0\tv1\tv2\tv3\tv4"},{"auxArity","0"},{"name","ReachableNullAtLine"},{"operation","output"},{"output-dir","."},{"params","{\"records\": {}, \"relation\": {\"arity\": 5, \"params\": [\"v0\", \"v1\", \"v2\", \"v3\", \"v4\"]}}"},{"types","{\"ADTs\": {}, \"records\": {}, \"relation\": {\"arity\": 5, \"types\": [\"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\"]}}"}});
if (!outputDirectoryArg.empty()) {directiveMap["output-dir"] = outputDirectoryArg;}
IOSystem::getInstance().getWriter(directiveMap, symTable, recordTable)->writeAll(*rel_8_ReachableNullAtLine);
} catch (std::exception& e) {std::cerr << e.what();exit(1);}
}
public:
void loadAll(std::string inputDirectoryArg = "") override {
}
public:
void dumpInputs() override {
}
public:
void dumpOutputs() override {
try {std::map<std::string, std::string> rwOperation;
rwOperation["IO"] = "stdout";
rwOperation["name"] = "ReachableNullAtLine";
rwOperation["types"] = "{\"relation\": {\"arity\": 5, \"auxArity\": 0, \"types\": [\"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\"]}}";
IOSystem::getInstance().getWriter(rwOperation, symTable, recordTable)->writeAll(*rel_8_ReachableNullAtLine);
} catch (std::exception& e) {std::cerr << e.what();exit(1);}
}
public:
SymbolTable& getSymbolTable() override {
return symTable;
}
RecordTable& getRecordTable() override {
return recordTable;
}
void setNumThreads(std::size_t numThreadsValue) override {
SouffleProgram::setNumThreads(numThreadsValue);
symTable.setNumLanes(getNumThreads());
recordTable.setNumLanes(getNumThreads());
}
void executeSubroutine(std::string name, const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) override {
if (name == "stratum_0") {
subroutine_0(args, ret);
return;}
if (name == "stratum_1") {
subroutine_1(args, ret);
return;}
if (name == "stratum_2") {
subroutine_2(args, ret);
return;}
if (name == "stratum_3") {
subroutine_3(args, ret);
return;}
if (name == "stratum_4") {
subroutine_4(args, ret);
return;}
if (name == "stratum_5") {
subroutine_5(args, ret);
return;}
if (name == "stratum_6") {
subroutine_6(args, ret);
return;}
if (name == "stratum_7") {
subroutine_7(args, ret);
return;}
fatal("unknown subroutine");
}
#ifdef _MSC_VER
#pragma warning(disable: 4100)
#endif // _MSC_VER
void subroutine_0(const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) {
signalHandler->setMsg(R"_(InstructionLine("<ArrayNullLoad: void <init>()>","1","-1","ArrayNullLoad.java").
in file original_program.dl [19:1-19:84])_");
[&](){
CREATE_OP_CONTEXT(rel_1_InstructionLine_op_ctxt,rel_1_InstructionLine->createContext());
Tuple<RamDomain,4> tuple{{ramBitCast(RamSigned(0)),ramBitCast(RamSigned(1)),ramBitCast(RamSigned(2)),ramBitCast(RamSigned(3))}};
rel_1_InstructionLine->insert(tuple,READ_OP_CONTEXT(rel_1_InstructionLine_op_ctxt));
}
();signalHandler->setMsg(R"_(InstructionLine("<ArrayNullLoad: void <init>()>","2","1","ArrayNullLoad.java").
in file original_program.dl [20:1-20:83])_");
[&](){
CREATE_OP_CONTEXT(rel_1_InstructionLine_op_ctxt,rel_1_InstructionLine->createContext());
Tuple<RamDomain,4> tuple{{ramBitCast(RamSigned(0)),ramBitCast(RamSigned(4)),ramBitCast(RamSigned(1)),ramBitCast(RamSigned(3))}};
rel_1_InstructionLine->insert(tuple,READ_OP_CONTEXT(rel_1_InstructionLine_op_ctxt));
}
();signalHandler->setMsg(R"_(InstructionLine("<ArrayNullLoad: void <init>()>","3","1","ArrayNullLoad.java").
in file original_program.dl [21:1-21:83])_");
[&](){
CREATE_OP_CONTEXT(rel_1_InstructionLine_op_ctxt,rel_1_InstructionLine->createContext());
Tuple<RamDomain,4> tuple{{ramBitCast(RamSigned(0)),ramBitCast(RamSigned(5)),ramBitCast(RamSigned(1)),ramBitCast(RamSigned(3))}};
rel_1_InstructionLine->insert(tuple,READ_OP_CONTEXT(rel_1_InstructionLine_op_ctxt));
}
();signalHandler->setMsg(R"_(InstructionLine("<ArrayNullLoad: void main(java.lang.String[])>","1","-1","ArrayNullLoad.java").
in file original_program.dl [22:1-22:100])_");
[&](){
CREATE_OP_CONTEXT(rel_1_InstructionLine_op_ctxt,rel_1_InstructionLine->createContext());
Tuple<RamDomain,4> tuple{{ramBitCast(RamSigned(6)),ramBitCast(RamSigned(1)),ramBitCast(RamSigned(2)),ramBitCast(RamSigned(3))}};
rel_1_InstructionLine->insert(tuple,READ_OP_CONTEXT(rel_1_InstructionLine_op_ctxt));
}
();signalHandler->setMsg(R"_(InstructionLine("<ArrayNullLoad: void main(java.lang.String[])>","2","3","ArrayNullLoad.java").
in file original_program.dl [23:1-23:99])_");
[&](){
CREATE_OP_CONTEXT(rel_1_InstructionLine_op_ctxt,rel_1_InstructionLine->createContext());
Tuple<RamDomain,4> tuple{{ramBitCast(RamSigned(6)),ramBitCast(RamSigned(4)),ramBitCast(RamSigned(5)),ramBitCast(RamSigned(3))}};
rel_1_InstructionLine->insert(tuple,READ_OP_CONTEXT(rel_1_InstructionLine_op_ctxt));
}
();signalHandler->setMsg(R"_(InstructionLine("<ArrayNullLoad: void main(java.lang.String[])>","3","4","ArrayNullLoad.java").
in file original_program.dl [24:1-24:99])_");
[&](){
CREATE_OP_CONTEXT(rel_1_InstructionLine_op_ctxt,rel_1_InstructionLine->createContext());
Tuple<RamDomain,4> tuple{{ramBitCast(RamSigned(6)),ramBitCast(RamSigned(5)),ramBitCast(RamSigned(7)),ramBitCast(RamSigned(3))}};
rel_1_InstructionLine->insert(tuple,READ_OP_CONTEXT(rel_1_InstructionLine_op_ctxt));
}
();signalHandler->setMsg(R"_(InstructionLine("<ArrayNullLoad: void main(java.lang.String[])>","4","4","ArrayNullLoad.java").
in file original_program.dl [25:1-25:99])_");
[&](){
CREATE_OP_CONTEXT(rel_1_InstructionLine_op_ctxt,rel_1_InstructionLine->createContext());
Tuple<RamDomain,4> tuple{{ramBitCast(RamSigned(6)),ramBitCast(RamSigned(7)),ramBitCast(RamSigned(7)),ramBitCast(RamSigned(3))}};
rel_1_InstructionLine->insert(tuple,READ_OP_CONTEXT(rel_1_InstructionLine_op_ctxt));
}
();signalHandler->setMsg(R"_(InstructionLine("<ArrayNullLoad: void main(java.lang.String[])>","5","5","ArrayNullLoad.java").
in file original_program.dl [26:1-26:99])_");
[&](){
CREATE_OP_CONTEXT(rel_1_InstructionLine_op_ctxt,rel_1_InstructionLine->createContext());
Tuple<RamDomain,4> tuple{{ramBitCast(RamSigned(6)),ramBitCast(RamSigned(8)),ramBitCast(RamSigned(8)),ramBitCast(RamSigned(3))}};
rel_1_InstructionLine->insert(tuple,READ_OP_CONTEXT(rel_1_InstructionLine_op_ctxt));
}
();}
#ifdef _MSC_VER
#pragma warning(default: 4100)
#endif // _MSC_VER
#ifdef _MSC_VER
#pragma warning(disable: 4100)
#endif // _MSC_VER
void subroutine_1(const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) {
signalHandler->setMsg(R"_(LoadArrayIndex("<ArrayNullLoad: void main(java.lang.String[])>/assign/instruction3","3","<ArrayNullLoad: void main(java.lang.String[])>/i#_4","<ArrayNullLoad: void main(java.lang.String[])>/array#_3","<ArrayNullLoad: void main(java.lang.String[])>").
in file original_program.dl [18:1-18:255])_");
[&](){
CREATE_OP_CONTEXT(rel_2_LoadArrayIndex_op_ctxt,rel_2_LoadArrayIndex->createContext());
Tuple<RamDomain,5> tuple{{ramBitCast(RamSigned(9)),ramBitCast(RamSigned(5)),ramBitCast(RamSigned(10)),ramBitCast(RamSigned(11)),ramBitCast(RamSigned(6))}};
rel_2_LoadArrayIndex->insert(tuple,READ_OP_CONTEXT(rel_2_LoadArrayIndex_op_ctxt));
}
();}
#ifdef _MSC_VER
#pragma warning(default: 4100)
#endif // _MSC_VER
#ifdef _MSC_VER
#pragma warning(disable: 4100)
#endif // _MSC_VER
void subroutine_2(const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) {
signalHandler->setMsg(R"_(VarPointsTo("<<unique-hcontext>>","<<main method array>>","4","<ArrayNullLoad: void main(java.lang.String[])>/@parameter0").
in file original_program.dl [27:1-27:128])_");
[&](){
CREATE_OP_CONTEXT(rel_3_VarPointsTo_op_ctxt,rel_3_VarPointsTo->createContext());
Tuple<RamDomain,4> tuple{{ramBitCast(RamSigned(12)),ramBitCast(RamSigned(13)),ramBitCast(RamSigned(7)),ramBitCast(RamSigned(14))}};
rel_3_VarPointsTo->insert(tuple,READ_OP_CONTEXT(rel_3_VarPointsTo_op_ctxt));
}
();signalHandler->setMsg(R"_(VarPointsTo("<<unique-hcontext>>","<<main method array>>","4","<ArrayNullLoad: void main(java.lang.String[])>/args#_0").
in file original_program.dl [28:1-28:124])_");
[&](){
CREATE_OP_CONTEXT(rel_3_VarPointsTo_op_ctxt,rel_3_VarPointsTo->createContext());
Tuple<RamDomain,4> tuple{{ramBitCast(RamSigned(12)),ramBitCast(RamSigned(13)),ramBitCast(RamSigned(7)),ramBitCast(RamSigned(15))}};
rel_3_VarPointsTo->insert(tuple,READ_OP_CONTEXT(rel_3_VarPointsTo_op_ctxt));
}
();signalHandler->setMsg(R"_(VarPointsTo("<<unique-hcontext>>","<<null pseudo heap>>","4","<ArrayNullLoad: void main(java.lang.String[])>/array#_3").
in file original_program.dl [29:1-29:124])_");
[&](){
CREATE_OP_CONTEXT(rel_3_VarPointsTo_op_ctxt,rel_3_VarPointsTo->createContext());
Tuple<RamDomain,4> tuple{{ramBitCast(RamSigned(12)),ramBitCast(RamSigned(16)),ramBitCast(RamSigned(7)),ramBitCast(RamSigned(11))}};
rel_3_VarPointsTo->insert(tuple,READ_OP_CONTEXT(rel_3_VarPointsTo_op_ctxt));
}
();}
#ifdef _MSC_VER
#pragma warning(default: 4100)
#endif // _MSC_VER
#ifdef _MSC_VER
#pragma warning(disable: 4100)
#endif // _MSC_VER
void subroutine_3(const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) {
signalHandler->setMsg(R"_(VarPointsToNull(var) :- 
   VarPointsTo(_,"<<null pseudo heap>>",_,var).
in file original_program.dl [12:1-12:72])_");
if(!(rel_3_VarPointsTo->empty())) {
[&](){
CREATE_OP_CONTEXT(rel_3_VarPointsTo_op_ctxt,rel_3_VarPointsTo->createContext());
CREATE_OP_CONTEXT(rel_4_VarPointsToNull_op_ctxt,rel_4_VarPointsToNull->createContext());
auto range = rel_3_VarPointsTo->lowerUpperRange_0100(Tuple<RamDomain,4>{{ramBitCast<RamDomain>(MIN_RAM_SIGNED), ramBitCast(RamSigned(16)), ramBitCast<RamDomain>(MIN_RAM_SIGNED), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,4>{{ramBitCast<RamDomain>(MAX_RAM_SIGNED), ramBitCast(RamSigned(16)), ramBitCast<RamDomain>(MAX_RAM_SIGNED), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_3_VarPointsTo_op_ctxt));
for(const auto& env0 : range) {
Tuple<RamDomain,1> tuple{{ramBitCast(env0[3])}};
rel_4_VarPointsToNull->insert(tuple,READ_OP_CONTEXT(rel_4_VarPointsToNull_op_ctxt));
}
}
();}
if (pruneImdtRels) rel_3_VarPointsTo->purge();
}
#ifdef _MSC_VER
#pragma warning(default: 4100)
#endif // _MSC_VER
#ifdef _MSC_VER
#pragma warning(disable: 4100)
#endif // _MSC_VER
void subroutine_4(const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) {
signalHandler->setMsg(R"_(NullAt(meth,index,"Load Array Index") :- 
   VarPointsToNull(var),
   LoadArrayIndex(_,index,_,var,meth).
in file original_program.dl [13:1-13:105])_");
if(!(rel_4_VarPointsToNull->empty()) && !(rel_2_LoadArrayIndex->empty())) {
[&](){
CREATE_OP_CONTEXT(rel_5_NullAt_op_ctxt,rel_5_NullAt->createContext());
CREATE_OP_CONTEXT(rel_2_LoadArrayIndex_op_ctxt,rel_2_LoadArrayIndex->createContext());
CREATE_OP_CONTEXT(rel_4_VarPointsToNull_op_ctxt,rel_4_VarPointsToNull->createContext());
for(const auto& env0 : *rel_4_VarPointsToNull) {
auto range = rel_2_LoadArrayIndex->lowerUpperRange_00010(Tuple<RamDomain,5>{{ramBitCast<RamDomain>(MIN_RAM_SIGNED), ramBitCast<RamDomain>(MIN_RAM_SIGNED), ramBitCast<RamDomain>(MIN_RAM_SIGNED), ramBitCast(env0[0]), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,5>{{ramBitCast<RamDomain>(MAX_RAM_SIGNED), ramBitCast<RamDomain>(MAX_RAM_SIGNED), ramBitCast<RamDomain>(MAX_RAM_SIGNED), ramBitCast(env0[0]), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_2_LoadArrayIndex_op_ctxt));
for(const auto& env1 : range) {
Tuple<RamDomain,3> tuple{{ramBitCast(env1[4]),ramBitCast(env1[1]),ramBitCast(RamSigned(17))}};
rel_5_NullAt->insert(tuple,READ_OP_CONTEXT(rel_5_NullAt_op_ctxt));
}
}
}
();}
if (pruneImdtRels) rel_2_LoadArrayIndex->purge();
if (pruneImdtRels) rel_4_VarPointsToNull->purge();
}
#ifdef _MSC_VER
#pragma warning(default: 4100)
#endif // _MSC_VER
#ifdef _MSC_VER
#pragma warning(disable: 4100)
#endif // _MSC_VER
void subroutine_5(const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) {
signalHandler->setMsg(R"_(Reachable("<ArrayNullLoad: void main(java.lang.String[])>").
in file original_program.dl [30:1-30:61])_");
[&](){
CREATE_OP_CONTEXT(rel_6_Reachable_op_ctxt,rel_6_Reachable->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(6))}};
rel_6_Reachable->insert(tuple,READ_OP_CONTEXT(rel_6_Reachable_op_ctxt));
}
();}
#ifdef _MSC_VER
#pragma warning(default: 4100)
#endif // _MSC_VER
#ifdef _MSC_VER
#pragma warning(disable: 4100)
#endif // _MSC_VER
void subroutine_6(const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) {
signalHandler->setMsg(R"_(ReachableNullAt(meth,index,type) :- 
   NullAt(meth,index,type),
   Reachable(meth).
in file original_program.dl [14:1-14:82])_");
if(!(rel_5_NullAt->empty()) && !(rel_6_Reachable->empty())) {
[&](){
CREATE_OP_CONTEXT(rel_5_NullAt_op_ctxt,rel_5_NullAt->createContext());
CREATE_OP_CONTEXT(rel_7_ReachableNullAt_op_ctxt,rel_7_ReachableNullAt->createContext());
CREATE_OP_CONTEXT(rel_6_Reachable_op_ctxt,rel_6_Reachable->createContext());
for(const auto& env0 : *rel_5_NullAt) {
if( rel_6_Reachable->contains(Tuple<RamDomain,1>{{ramBitCast(env0[0])}},READ_OP_CONTEXT(rel_6_Reachable_op_ctxt))) {
Tuple<RamDomain,3> tuple{{ramBitCast(env0[0]),ramBitCast(env0[1]),ramBitCast(env0[2])}};
rel_7_ReachableNullAt->insert(tuple,READ_OP_CONTEXT(rel_7_ReachableNullAt_op_ctxt));
}
}
}
();}
if (pruneImdtRels) rel_6_Reachable->purge();
if (pruneImdtRels) rel_5_NullAt->purge();
}
#ifdef _MSC_VER
#pragma warning(default: 4100)
#endif // _MSC_VER
#ifdef _MSC_VER
#pragma warning(disable: 4100)
#endif // _MSC_VER
void subroutine_7(const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) {
signalHandler->setMsg(R"_(ReachableNullAtLine(meth,index,file,line,type) :- 
   ReachableNullAt(meth,index,type),
   InstructionLine(meth,index,line,file).
in file original_program.dl [15:1-15:132])_");
if(!(rel_7_ReachableNullAt->empty()) && !(rel_1_InstructionLine->empty())) {
[&](){
CREATE_OP_CONTEXT(rel_7_ReachableNullAt_op_ctxt,rel_7_ReachableNullAt->createContext());
CREATE_OP_CONTEXT(rel_1_InstructionLine_op_ctxt,rel_1_InstructionLine->createContext());
CREATE_OP_CONTEXT(rel_8_ReachableNullAtLine_op_ctxt,rel_8_ReachableNullAtLine->createContext());
for(const auto& env0 : *rel_7_ReachableNullAt) {
auto range = rel_1_InstructionLine->lowerUpperRange_1100(Tuple<RamDomain,4>{{ramBitCast(env0[0]), ramBitCast(env0[1]), ramBitCast<RamDomain>(MIN_RAM_SIGNED), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,4>{{ramBitCast(env0[0]), ramBitCast(env0[1]), ramBitCast<RamDomain>(MAX_RAM_SIGNED), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_1_InstructionLine_op_ctxt));
for(const auto& env1 : range) {
Tuple<RamDomain,5> tuple{{ramBitCast(env0[0]),ramBitCast(env0[1]),ramBitCast(env1[3]),ramBitCast(env1[2]),ramBitCast(env0[2])}};
rel_8_ReachableNullAtLine->insert(tuple,READ_OP_CONTEXT(rel_8_ReachableNullAtLine_op_ctxt));
}
}
}
();}
if (performIO) {
try {std::map<std::string, std::string> directiveMap({{"IO","file"},{"attributeNames","v0\tv1\tv2\tv3\tv4"},{"auxArity","0"},{"name","ReachableNullAtLine"},{"operation","output"},{"output-dir","."},{"params","{\"records\": {}, \"relation\": {\"arity\": 5, \"params\": [\"v0\", \"v1\", \"v2\", \"v3\", \"v4\"]}}"},{"types","{\"ADTs\": {}, \"records\": {}, \"relation\": {\"arity\": 5, \"types\": [\"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\"]}}"}});
if (!outputDirectory.empty()) {directiveMap["output-dir"] = outputDirectory;}
IOSystem::getInstance().getWriter(directiveMap, symTable, recordTable)->writeAll(*rel_8_ReachableNullAtLine);
} catch (std::exception& e) {std::cerr << e.what();exit(1);}
}
if (pruneImdtRels) rel_1_InstructionLine->purge();
if (pruneImdtRels) rel_7_ReachableNullAt->purge();
}
#ifdef _MSC_VER
#pragma warning(default: 4100)
#endif // _MSC_VER
};
SouffleProgram *newInstance_original(){return new Sf_original;}
SymbolTable *getST_original(SouffleProgram *p){return &reinterpret_cast<Sf_original*>(p)->getSymbolTable();}

#ifdef __EMBEDDED_SOUFFLE__
class factory_Sf_original: public souffle::ProgramFactory {
SouffleProgram *newInstance() {
return new Sf_original();
};
public:
factory_Sf_original() : ProgramFactory("original"){}
};
extern "C" {
factory_Sf_original __factory_Sf_original_instance;
}
}
#else
}
int main(int argc, char** argv)
{
try{
souffle::CmdOptions opt(R"(original_program.dl)",
R"()",
R"()",
false,
R"()",
1);
if (!opt.parse(argc,argv)) return 1;
souffle::Sf_original obj;
#if defined(_OPENMP) 
obj.setNumThreads(opt.getNumJobs());

#endif
obj.runAll(opt.getInputFileDir(), opt.getOutputFileDir());
return 0;
} catch(std::exception &e) { souffle::SignalHandler::instance()->error(e.what());}
}

#endif


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
struct t_btree_iiiiiiii__1_0_2_3_4_5_6_7__01000000__11111111 {
static constexpr Relation::arity_type Arity = 8;
using t_tuple = Tuple<RamDomain, 8>;
Table<t_tuple> dataTable;
Lock insert_lock;
struct t_comparator_0{
 int operator()(const t_tuple *a, const t_tuple *b) const {
  return (ramBitCast<RamSigned>((*a)[1]) <ramBitCast<RamSigned> ((*b)[1])) ? -1 : ((ramBitCast<RamSigned>((*a)[1]) > ramBitCast<RamSigned>((*b)[1])) ? 1 :((ramBitCast<RamSigned>((*a)[0]) <ramBitCast<RamSigned> ((*b)[0])) ? -1 : ((ramBitCast<RamSigned>((*a)[0]) > ramBitCast<RamSigned>((*b)[0])) ? 1 :((ramBitCast<RamSigned>((*a)[2]) <ramBitCast<RamSigned> ((*b)[2])) ? -1 : ((ramBitCast<RamSigned>((*a)[2]) > ramBitCast<RamSigned>((*b)[2])) ? 1 :((ramBitCast<RamSigned>((*a)[3]) <ramBitCast<RamSigned> ((*b)[3])) ? -1 : ((ramBitCast<RamSigned>((*a)[3]) > ramBitCast<RamSigned>((*b)[3])) ? 1 :((ramBitCast<RamSigned>((*a)[4]) <ramBitCast<RamSigned> ((*b)[4])) ? -1 : ((ramBitCast<RamSigned>((*a)[4]) > ramBitCast<RamSigned>((*b)[4])) ? 1 :((ramBitCast<RamSigned>((*a)[5]) <ramBitCast<RamSigned> ((*b)[5])) ? -1 : ((ramBitCast<RamSigned>((*a)[5]) > ramBitCast<RamSigned>((*b)[5])) ? 1 :((ramBitCast<RamSigned>((*a)[6]) <ramBitCast<RamSigned> ((*b)[6])) ? -1 : ((ramBitCast<RamSigned>((*a)[6]) > ramBitCast<RamSigned>((*b)[6])) ? 1 :((ramBitCast<RamSigned>((*a)[7]) <ramBitCast<RamSigned> ((*b)[7])) ? -1 : ((ramBitCast<RamSigned>((*a)[7]) > ramBitCast<RamSigned>((*b)[7])) ? 1 :(0))))))))))))))));
 }
bool less(const t_tuple *a, const t_tuple *b) const {
  return ramBitCast<RamSigned> ((*a)[1]) < ramBitCast<RamSigned>((*b)[1])|| ((ramBitCast<RamSigned>((*a)[1]) == ramBitCast<RamSigned>((*b)[1]) && (ramBitCast<RamSigned> ((*a)[0]) < ramBitCast<RamSigned>((*b)[0])|| ((ramBitCast<RamSigned>((*a)[0]) == ramBitCast<RamSigned>((*b)[0]) && (ramBitCast<RamSigned> ((*a)[2]) < ramBitCast<RamSigned>((*b)[2])|| ((ramBitCast<RamSigned>((*a)[2]) == ramBitCast<RamSigned>((*b)[2]) && (ramBitCast<RamSigned> ((*a)[3]) < ramBitCast<RamSigned>((*b)[3])|| ((ramBitCast<RamSigned>((*a)[3]) == ramBitCast<RamSigned>((*b)[3]) && (ramBitCast<RamSigned> ((*a)[4]) < ramBitCast<RamSigned>((*b)[4])|| ((ramBitCast<RamSigned>((*a)[4]) == ramBitCast<RamSigned>((*b)[4]) && (ramBitCast<RamSigned> ((*a)[5]) < ramBitCast<RamSigned>((*b)[5])|| ((ramBitCast<RamSigned>((*a)[5]) == ramBitCast<RamSigned>((*b)[5]) && (ramBitCast<RamSigned> ((*a)[6]) < ramBitCast<RamSigned>((*b)[6])|| ((ramBitCast<RamSigned>((*a)[6]) == ramBitCast<RamSigned>((*b)[6]) && (ramBitCast<RamSigned> ((*a)[7]) < ramBitCast<RamSigned>((*b)[7]))))))))))))))))))))));
 }
bool equal(const t_tuple *a, const t_tuple *b) const {
return ramBitCast<RamSigned>((*a)[1]) == ramBitCast<RamSigned>((*b)[1])&&ramBitCast<RamSigned>((*a)[0]) == ramBitCast<RamSigned>((*b)[0])&&ramBitCast<RamSigned>((*a)[2]) == ramBitCast<RamSigned>((*b)[2])&&ramBitCast<RamSigned>((*a)[3]) == ramBitCast<RamSigned>((*b)[3])&&ramBitCast<RamSigned>((*a)[4]) == ramBitCast<RamSigned>((*b)[4])&&ramBitCast<RamSigned>((*a)[5]) == ramBitCast<RamSigned>((*b)[5])&&ramBitCast<RamSigned>((*a)[6]) == ramBitCast<RamSigned>((*b)[6])&&ramBitCast<RamSigned>((*a)[7]) == ramBitCast<RamSigned>((*b)[7]);
 }
};
using t_ind_0 = btree_set<const t_tuple*,t_comparator_0>;
t_ind_0 ind_0;
using iterator_0 = IterDerefWrapper<typename t_ind_0::iterator>;
using iterator = iterator_0;
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
const t_tuple* masterCopy = nullptr;
{
auto lease = insert_lock.acquire();
if (contains(t, h)) return false;
masterCopy = &dataTable.insert(t);
ind_0.insert(masterCopy, h.hints_0_lower);
}
return true;
}
bool insert(const RamDomain* ramDomain) {
RamDomain data[8];
std::copy(ramDomain, ramDomain + 8, data);
const t_tuple& tuple = reinterpret_cast<const t_tuple&>(data);
context h;
return insert(tuple, h);
}
bool insert(RamDomain a0,RamDomain a1,RamDomain a2,RamDomain a3,RamDomain a4,RamDomain a5,RamDomain a6,RamDomain a7) {
RamDomain data[8] = {a0,a1,a2,a3,a4,a5,a6,a7};
return insert(data);
}
bool contains(const t_tuple& t, context& h) const {
return ind_0.contains(&t, h.hints_0_lower);
}
bool contains(const t_tuple& t) const {
context h;
return contains(t, h);
}
std::size_t size() const {
return ind_0.size();
}
iterator find(const t_tuple& t, context& h) const {
return ind_0.find(&t, h.hints_0_lower);
}
iterator find(const t_tuple& t) const {
context h;
return find(t, h);
}
range<iterator> lowerUpperRange_0(const t_tuple& lower, const t_tuple& upper, context& h) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<iterator> lowerUpperRange_0(const t_tuple& lower, const t_tuple& upper) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<iterator_0> lowerUpperRange_01000000(const t_tuple& lower, const t_tuple& upper, context& h) const {
t_comparator_0 comparator;
int cmp = comparator(&lower, &upper);
if (cmp > 0) {
    return range<iterator_0>(ind_0.end(), ind_0.end());
}
return range<iterator_0>(ind_0.lower_bound(&lower, h.hints_0_lower), ind_0.upper_bound(&upper, h.hints_0_upper));
}
range<iterator_0> lowerUpperRange_01000000(const t_tuple& lower, const t_tuple& upper) const {
context h;
return lowerUpperRange_01000000(lower, upper, h);
}
range<iterator_0> lowerUpperRange_11111111(const t_tuple& lower, const t_tuple& upper, context& h) const {
t_comparator_0 comparator;
int cmp = comparator(&lower, &upper);
if (cmp == 0) {
    auto pos = ind_0.find(&lower, h.hints_0_lower);
    auto fin = ind_0.end();
    if (pos != fin) {fin = pos; ++fin;}
    return range<iterator_0>(pos, fin);
}
if (cmp > 0) {
    return range<iterator_0>(ind_0.end(), ind_0.end());
}
return range<iterator_0>(ind_0.lower_bound(&lower, h.hints_0_lower), ind_0.upper_bound(&upper, h.hints_0_upper));
}
range<iterator_0> lowerUpperRange_11111111(const t_tuple& lower, const t_tuple& upper) const {
context h;
return lowerUpperRange_11111111(lower, upper, h);
}
bool empty() const {
return ind_0.empty();
}
std::vector<range<iterator>> partition() const {
std::vector<range<iterator>> res;
for (const auto& cur : ind_0.getChunks(400)) {
    res.push_back(make_range(derefIter(cur.begin()), derefIter(cur.end())));
}
return res;
}
void purge() {
ind_0.clear();
dataTable.clear();
}
iterator begin() const {
return ind_0.begin();
}
iterator end() const {
return ind_0.end();
}
void printStatistics(std::ostream& o) const {
o << " arity 8 indirect b-tree index 0 lex-order [1,0,2,3,4,5,6,7]\n";
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
struct t_btree_iiiiiii__0_1_2_3_4_5_6__1111111 {
static constexpr Relation::arity_type Arity = 7;
using t_tuple = Tuple<RamDomain, 7>;
Table<t_tuple> dataTable;
Lock insert_lock;
struct t_comparator_0{
 int operator()(const t_tuple *a, const t_tuple *b) const {
  return (ramBitCast<RamSigned>((*a)[0]) <ramBitCast<RamSigned> ((*b)[0])) ? -1 : ((ramBitCast<RamSigned>((*a)[0]) > ramBitCast<RamSigned>((*b)[0])) ? 1 :((ramBitCast<RamSigned>((*a)[1]) <ramBitCast<RamSigned> ((*b)[1])) ? -1 : ((ramBitCast<RamSigned>((*a)[1]) > ramBitCast<RamSigned>((*b)[1])) ? 1 :((ramBitCast<RamSigned>((*a)[2]) <ramBitCast<RamSigned> ((*b)[2])) ? -1 : ((ramBitCast<RamSigned>((*a)[2]) > ramBitCast<RamSigned>((*b)[2])) ? 1 :((ramBitCast<RamSigned>((*a)[3]) <ramBitCast<RamSigned> ((*b)[3])) ? -1 : ((ramBitCast<RamSigned>((*a)[3]) > ramBitCast<RamSigned>((*b)[3])) ? 1 :((ramBitCast<RamSigned>((*a)[4]) <ramBitCast<RamSigned> ((*b)[4])) ? -1 : ((ramBitCast<RamSigned>((*a)[4]) > ramBitCast<RamSigned>((*b)[4])) ? 1 :((ramBitCast<RamSigned>((*a)[5]) <ramBitCast<RamSigned> ((*b)[5])) ? -1 : ((ramBitCast<RamSigned>((*a)[5]) > ramBitCast<RamSigned>((*b)[5])) ? 1 :((ramBitCast<RamSigned>((*a)[6]) <ramBitCast<RamSigned> ((*b)[6])) ? -1 : ((ramBitCast<RamSigned>((*a)[6]) > ramBitCast<RamSigned>((*b)[6])) ? 1 :(0))))))))))))));
 }
bool less(const t_tuple *a, const t_tuple *b) const {
  return ramBitCast<RamSigned> ((*a)[0]) < ramBitCast<RamSigned>((*b)[0])|| ((ramBitCast<RamSigned>((*a)[0]) == ramBitCast<RamSigned>((*b)[0]) && (ramBitCast<RamSigned> ((*a)[1]) < ramBitCast<RamSigned>((*b)[1])|| ((ramBitCast<RamSigned>((*a)[1]) == ramBitCast<RamSigned>((*b)[1]) && (ramBitCast<RamSigned> ((*a)[2]) < ramBitCast<RamSigned>((*b)[2])|| ((ramBitCast<RamSigned>((*a)[2]) == ramBitCast<RamSigned>((*b)[2]) && (ramBitCast<RamSigned> ((*a)[3]) < ramBitCast<RamSigned>((*b)[3])|| ((ramBitCast<RamSigned>((*a)[3]) == ramBitCast<RamSigned>((*b)[3]) && (ramBitCast<RamSigned> ((*a)[4]) < ramBitCast<RamSigned>((*b)[4])|| ((ramBitCast<RamSigned>((*a)[4]) == ramBitCast<RamSigned>((*b)[4]) && (ramBitCast<RamSigned> ((*a)[5]) < ramBitCast<RamSigned>((*b)[5])|| ((ramBitCast<RamSigned>((*a)[5]) == ramBitCast<RamSigned>((*b)[5]) && (ramBitCast<RamSigned> ((*a)[6]) < ramBitCast<RamSigned>((*b)[6])))))))))))))))))));
 }
bool equal(const t_tuple *a, const t_tuple *b) const {
return ramBitCast<RamSigned>((*a)[0]) == ramBitCast<RamSigned>((*b)[0])&&ramBitCast<RamSigned>((*a)[1]) == ramBitCast<RamSigned>((*b)[1])&&ramBitCast<RamSigned>((*a)[2]) == ramBitCast<RamSigned>((*b)[2])&&ramBitCast<RamSigned>((*a)[3]) == ramBitCast<RamSigned>((*b)[3])&&ramBitCast<RamSigned>((*a)[4]) == ramBitCast<RamSigned>((*b)[4])&&ramBitCast<RamSigned>((*a)[5]) == ramBitCast<RamSigned>((*b)[5])&&ramBitCast<RamSigned>((*a)[6]) == ramBitCast<RamSigned>((*b)[6]);
 }
};
using t_ind_0 = btree_set<const t_tuple*,t_comparator_0>;
t_ind_0 ind_0;
using iterator_0 = IterDerefWrapper<typename t_ind_0::iterator>;
using iterator = iterator_0;
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
const t_tuple* masterCopy = nullptr;
{
auto lease = insert_lock.acquire();
if (contains(t, h)) return false;
masterCopy = &dataTable.insert(t);
ind_0.insert(masterCopy, h.hints_0_lower);
}
return true;
}
bool insert(const RamDomain* ramDomain) {
RamDomain data[7];
std::copy(ramDomain, ramDomain + 7, data);
const t_tuple& tuple = reinterpret_cast<const t_tuple&>(data);
context h;
return insert(tuple, h);
}
bool insert(RamDomain a0,RamDomain a1,RamDomain a2,RamDomain a3,RamDomain a4,RamDomain a5,RamDomain a6) {
RamDomain data[7] = {a0,a1,a2,a3,a4,a5,a6};
return insert(data);
}
bool contains(const t_tuple& t, context& h) const {
return ind_0.contains(&t, h.hints_0_lower);
}
bool contains(const t_tuple& t) const {
context h;
return contains(t, h);
}
std::size_t size() const {
return ind_0.size();
}
iterator find(const t_tuple& t, context& h) const {
return ind_0.find(&t, h.hints_0_lower);
}
iterator find(const t_tuple& t) const {
context h;
return find(t, h);
}
range<iterator> lowerUpperRange_0(const t_tuple& lower, const t_tuple& upper, context& h) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<iterator> lowerUpperRange_0(const t_tuple& lower, const t_tuple& upper) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<iterator_0> lowerUpperRange_1111111(const t_tuple& lower, const t_tuple& upper, context& h) const {
t_comparator_0 comparator;
int cmp = comparator(&lower, &upper);
if (cmp == 0) {
    auto pos = ind_0.find(&lower, h.hints_0_lower);
    auto fin = ind_0.end();
    if (pos != fin) {fin = pos; ++fin;}
    return range<iterator_0>(pos, fin);
}
if (cmp > 0) {
    return range<iterator_0>(ind_0.end(), ind_0.end());
}
return range<iterator_0>(ind_0.lower_bound(&lower, h.hints_0_lower), ind_0.upper_bound(&upper, h.hints_0_upper));
}
range<iterator_0> lowerUpperRange_1111111(const t_tuple& lower, const t_tuple& upper) const {
context h;
return lowerUpperRange_1111111(lower, upper, h);
}
bool empty() const {
return ind_0.empty();
}
std::vector<range<iterator>> partition() const {
std::vector<range<iterator>> res;
for (const auto& cur : ind_0.getChunks(400)) {
    res.push_back(make_range(derefIter(cur.begin()), derefIter(cur.end())));
}
return res;
}
void purge() {
ind_0.clear();
dataTable.clear();
}
iterator begin() const {
return ind_0.begin();
}
iterator end() const {
return ind_0.end();
}
void printStatistics(std::ostream& o) const {
o << " arity 7 indirect b-tree index 0 lex-order [0,1,2,3,4,5,6]\n";
ind_0.printStats(o);
}
};
struct t_btree_iiiiiiiii__0_1_2_3_4_5_6_7_8__111111111 {
static constexpr Relation::arity_type Arity = 9;
using t_tuple = Tuple<RamDomain, 9>;
Table<t_tuple> dataTable;
Lock insert_lock;
struct t_comparator_0{
 int operator()(const t_tuple *a, const t_tuple *b) const {
  return (ramBitCast<RamSigned>((*a)[0]) <ramBitCast<RamSigned> ((*b)[0])) ? -1 : ((ramBitCast<RamSigned>((*a)[0]) > ramBitCast<RamSigned>((*b)[0])) ? 1 :((ramBitCast<RamSigned>((*a)[1]) <ramBitCast<RamSigned> ((*b)[1])) ? -1 : ((ramBitCast<RamSigned>((*a)[1]) > ramBitCast<RamSigned>((*b)[1])) ? 1 :((ramBitCast<RamSigned>((*a)[2]) <ramBitCast<RamSigned> ((*b)[2])) ? -1 : ((ramBitCast<RamSigned>((*a)[2]) > ramBitCast<RamSigned>((*b)[2])) ? 1 :((ramBitCast<RamSigned>((*a)[3]) <ramBitCast<RamSigned> ((*b)[3])) ? -1 : ((ramBitCast<RamSigned>((*a)[3]) > ramBitCast<RamSigned>((*b)[3])) ? 1 :((ramBitCast<RamSigned>((*a)[4]) <ramBitCast<RamSigned> ((*b)[4])) ? -1 : ((ramBitCast<RamSigned>((*a)[4]) > ramBitCast<RamSigned>((*b)[4])) ? 1 :((ramBitCast<RamSigned>((*a)[5]) <ramBitCast<RamSigned> ((*b)[5])) ? -1 : ((ramBitCast<RamSigned>((*a)[5]) > ramBitCast<RamSigned>((*b)[5])) ? 1 :((ramBitCast<RamSigned>((*a)[6]) <ramBitCast<RamSigned> ((*b)[6])) ? -1 : ((ramBitCast<RamSigned>((*a)[6]) > ramBitCast<RamSigned>((*b)[6])) ? 1 :((ramBitCast<RamSigned>((*a)[7]) <ramBitCast<RamSigned> ((*b)[7])) ? -1 : ((ramBitCast<RamSigned>((*a)[7]) > ramBitCast<RamSigned>((*b)[7])) ? 1 :((ramBitCast<RamSigned>((*a)[8]) <ramBitCast<RamSigned> ((*b)[8])) ? -1 : ((ramBitCast<RamSigned>((*a)[8]) > ramBitCast<RamSigned>((*b)[8])) ? 1 :(0))))))))))))))))));
 }
bool less(const t_tuple *a, const t_tuple *b) const {
  return ramBitCast<RamSigned> ((*a)[0]) < ramBitCast<RamSigned>((*b)[0])|| ((ramBitCast<RamSigned>((*a)[0]) == ramBitCast<RamSigned>((*b)[0]) && (ramBitCast<RamSigned> ((*a)[1]) < ramBitCast<RamSigned>((*b)[1])|| ((ramBitCast<RamSigned>((*a)[1]) == ramBitCast<RamSigned>((*b)[1]) && (ramBitCast<RamSigned> ((*a)[2]) < ramBitCast<RamSigned>((*b)[2])|| ((ramBitCast<RamSigned>((*a)[2]) == ramBitCast<RamSigned>((*b)[2]) && (ramBitCast<RamSigned> ((*a)[3]) < ramBitCast<RamSigned>((*b)[3])|| ((ramBitCast<RamSigned>((*a)[3]) == ramBitCast<RamSigned>((*b)[3]) && (ramBitCast<RamSigned> ((*a)[4]) < ramBitCast<RamSigned>((*b)[4])|| ((ramBitCast<RamSigned>((*a)[4]) == ramBitCast<RamSigned>((*b)[4]) && (ramBitCast<RamSigned> ((*a)[5]) < ramBitCast<RamSigned>((*b)[5])|| ((ramBitCast<RamSigned>((*a)[5]) == ramBitCast<RamSigned>((*b)[5]) && (ramBitCast<RamSigned> ((*a)[6]) < ramBitCast<RamSigned>((*b)[6])|| ((ramBitCast<RamSigned>((*a)[6]) == ramBitCast<RamSigned>((*b)[6]) && (ramBitCast<RamSigned> ((*a)[7]) < ramBitCast<RamSigned>((*b)[7])|| ((ramBitCast<RamSigned>((*a)[7]) == ramBitCast<RamSigned>((*b)[7]) && (ramBitCast<RamSigned> ((*a)[8]) < ramBitCast<RamSigned>((*b)[8])))))))))))))))))))))))));
 }
bool equal(const t_tuple *a, const t_tuple *b) const {
return ramBitCast<RamSigned>((*a)[0]) == ramBitCast<RamSigned>((*b)[0])&&ramBitCast<RamSigned>((*a)[1]) == ramBitCast<RamSigned>((*b)[1])&&ramBitCast<RamSigned>((*a)[2]) == ramBitCast<RamSigned>((*b)[2])&&ramBitCast<RamSigned>((*a)[3]) == ramBitCast<RamSigned>((*b)[3])&&ramBitCast<RamSigned>((*a)[4]) == ramBitCast<RamSigned>((*b)[4])&&ramBitCast<RamSigned>((*a)[5]) == ramBitCast<RamSigned>((*b)[5])&&ramBitCast<RamSigned>((*a)[6]) == ramBitCast<RamSigned>((*b)[6])&&ramBitCast<RamSigned>((*a)[7]) == ramBitCast<RamSigned>((*b)[7])&&ramBitCast<RamSigned>((*a)[8]) == ramBitCast<RamSigned>((*b)[8]);
 }
};
using t_ind_0 = btree_set<const t_tuple*,t_comparator_0>;
t_ind_0 ind_0;
using iterator_0 = IterDerefWrapper<typename t_ind_0::iterator>;
using iterator = iterator_0;
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
const t_tuple* masterCopy = nullptr;
{
auto lease = insert_lock.acquire();
if (contains(t, h)) return false;
masterCopy = &dataTable.insert(t);
ind_0.insert(masterCopy, h.hints_0_lower);
}
return true;
}
bool insert(const RamDomain* ramDomain) {
RamDomain data[9];
std::copy(ramDomain, ramDomain + 9, data);
const t_tuple& tuple = reinterpret_cast<const t_tuple&>(data);
context h;
return insert(tuple, h);
}
bool insert(RamDomain a0,RamDomain a1,RamDomain a2,RamDomain a3,RamDomain a4,RamDomain a5,RamDomain a6,RamDomain a7,RamDomain a8) {
RamDomain data[9] = {a0,a1,a2,a3,a4,a5,a6,a7,a8};
return insert(data);
}
bool contains(const t_tuple& t, context& h) const {
return ind_0.contains(&t, h.hints_0_lower);
}
bool contains(const t_tuple& t) const {
context h;
return contains(t, h);
}
std::size_t size() const {
return ind_0.size();
}
iterator find(const t_tuple& t, context& h) const {
return ind_0.find(&t, h.hints_0_lower);
}
iterator find(const t_tuple& t) const {
context h;
return find(t, h);
}
range<iterator> lowerUpperRange_0(const t_tuple& lower, const t_tuple& upper, context& h) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<iterator> lowerUpperRange_0(const t_tuple& lower, const t_tuple& upper) const {
return range<iterator>(ind_0.begin(),ind_0.end());
}
range<iterator_0> lowerUpperRange_111111111(const t_tuple& lower, const t_tuple& upper, context& h) const {
t_comparator_0 comparator;
int cmp = comparator(&lower, &upper);
if (cmp == 0) {
    auto pos = ind_0.find(&lower, h.hints_0_lower);
    auto fin = ind_0.end();
    if (pos != fin) {fin = pos; ++fin;}
    return range<iterator_0>(pos, fin);
}
if (cmp > 0) {
    return range<iterator_0>(ind_0.end(), ind_0.end());
}
return range<iterator_0>(ind_0.lower_bound(&lower, h.hints_0_lower), ind_0.upper_bound(&upper, h.hints_0_upper));
}
range<iterator_0> lowerUpperRange_111111111(const t_tuple& lower, const t_tuple& upper) const {
context h;
return lowerUpperRange_111111111(lower, upper, h);
}
bool empty() const {
return ind_0.empty();
}
std::vector<range<iterator>> partition() const {
std::vector<range<iterator>> res;
for (const auto& cur : ind_0.getChunks(400)) {
    res.push_back(make_range(derefIter(cur.begin()), derefIter(cur.end())));
}
return res;
}
void purge() {
ind_0.clear();
dataTable.clear();
}
iterator begin() const {
return ind_0.begin();
}
iterator end() const {
return ind_0.end();
}
void printStatistics(std::ostream& o) const {
o << " arity 9 indirect b-tree index 0 lex-order [0,1,2,3,4,5,6,7,8]\n";
ind_0.printStats(o);
}
};

class Sf_small_transformed : public SouffleProgram {
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
	R"_([symlog_symbolic_0, symlog_symbolic_1, symlog_symbolic_2, symlog_symbolic_3],  eq/neq )_",
	R"_([symlog_symbolic_0, symlog_symbolic_1, symlog_symbolic_2],  eq/neq , [symlog_symbolic_3])_",
	R"_([symlog_symbolic_0, symlog_symbolic_1, symlog_symbolic_3],  eq/neq , [symlog_symbolic_2])_",
	R"_([symlog_symbolic_0, symlog_symbolic_1],  eq/neq , [symlog_symbolic_2, symlog_symbolic_3])_",
	R"_([symlog_symbolic_0, symlog_symbolic_2, symlog_symbolic_3],  eq/neq , [symlog_symbolic_1])_",
	R"_([symlog_symbolic_0, symlog_symbolic_2],  eq/neq , [symlog_symbolic_1, symlog_symbolic_3])_",
	R"_([symlog_symbolic_0, symlog_symbolic_3],  eq/neq , [symlog_symbolic_1, symlog_symbolic_2])_",
	R"_([symlog_symbolic_0],  eq/neq , [symlog_symbolic_1, symlog_symbolic_2, symlog_symbolic_3])_",
	R"_(<<main method array>>)_",
	R"_(<<null pseudo heap>>)_",
	R"_([symlog_symbolic_1],  eq/neq , [symlog_symbolic_0, symlog_symbolic_2, symlog_symbolic_3])_",
	R"_([symlog_symbolic_1, symlog_symbolic_3],  eq/neq , [symlog_symbolic_0, symlog_symbolic_2])_",
	R"_([symlog_symbolic_1, symlog_symbolic_2],  eq/neq , [symlog_symbolic_0, symlog_symbolic_3])_",
	R"_([symlog_symbolic_1, symlog_symbolic_2, symlog_symbolic_3],  eq/neq , [symlog_symbolic_0])_",
	R"_([symlog_symbolic_2],  eq/neq , [symlog_symbolic_0, symlog_symbolic_1, symlog_symbolic_3])_",
	R"_([symlog_symbolic_2, symlog_symbolic_3],  eq/neq , [symlog_symbolic_0, symlog_symbolic_1])_",
	R"_(symlog_symbolic_0)_",
	R"_(<ArrayNullLoad: void main(java.lang.String[])>/@parameter0)_",
	R"_(<ArrayNullLoad: void main(java.lang.String[])>/args#_0)_",
	R"_([symlog_symbolic_3],  eq/neq , [symlog_symbolic_0, symlog_symbolic_1, symlog_symbolic_2])_",
	R"_(Load Array Index)_",
};// -- initialize record table --
SpecializedRecordTable<0> recordTable{};
// -- Table: InstructionLine
Own<t_btree_iiii__0_1_2_3__1111__1100> rel_1_InstructionLine = mk<t_btree_iiii__0_1_2_3__1111__1100>();
souffle::RelationWrapper<t_btree_iiii__0_1_2_3__1111__1100> wrapper_rel_1_InstructionLine;
// -- Table: LoadArrayIndex
Own<t_btree_iiiii__3_0_1_2_4__11111__00010> rel_2_LoadArrayIndex = mk<t_btree_iiiii__3_0_1_2_4__11111__00010>();
souffle::RelationWrapper<t_btree_iiiii__3_0_1_2_4__11111__00010> wrapper_rel_2_LoadArrayIndex;
// -- Table: symlog_domain_symlog_symbolic_0
Own<t_btree_i__0__1> rel_3_symlog_domain_symlog_symbolic_0 = mk<t_btree_i__0__1>();
souffle::RelationWrapper<t_btree_i__0__1> wrapper_rel_3_symlog_domain_symlog_symbolic_0;
// -- Table: symlog_domain_symlog_symbolic_1
Own<t_btree_i__0__1> rel_4_symlog_domain_symlog_symbolic_1 = mk<t_btree_i__0__1>();
souffle::RelationWrapper<t_btree_i__0__1> wrapper_rel_4_symlog_domain_symlog_symbolic_1;
// -- Table: symlog_domain_symlog_symbolic_2
Own<t_btree_i__0__1> rel_5_symlog_domain_symlog_symbolic_2 = mk<t_btree_i__0__1>();
souffle::RelationWrapper<t_btree_i__0__1> wrapper_rel_5_symlog_domain_symlog_symbolic_2;
// -- Table: symlog_domain_symlog_symbolic_3
Own<t_btree_i__0__1> rel_6_symlog_domain_symlog_symbolic_3 = mk<t_btree_i__0__1>();
souffle::RelationWrapper<t_btree_i__0__1> wrapper_rel_6_symlog_domain_symlog_symbolic_3;
// -- Table: VarPointsTo
Own<t_btree_iiiiiiii__1_0_2_3_4_5_6_7__01000000__11111111> rel_7_VarPointsTo = mk<t_btree_iiiiiiii__1_0_2_3_4_5_6_7__01000000__11111111>();
souffle::RelationWrapper<t_btree_iiiiiiii__1_0_2_3_4_5_6_7__01000000__11111111> wrapper_rel_7_VarPointsTo;
// -- Table: VarPointsToNull
Own<t_btree_iiiii__0_1_2_3_4__11111> rel_8_VarPointsToNull = mk<t_btree_iiiii__0_1_2_3_4__11111>();
souffle::RelationWrapper<t_btree_iiiii__0_1_2_3_4__11111> wrapper_rel_8_VarPointsToNull;
// -- Table: NullAt
Own<t_btree_iiiiiii__0_1_2_3_4_5_6__1111111> rel_9_NullAt = mk<t_btree_iiiiiii__0_1_2_3_4_5_6__1111111>();
souffle::RelationWrapper<t_btree_iiiiiii__0_1_2_3_4_5_6__1111111> wrapper_rel_9_NullAt;
// -- Table: Reachable
Own<t_btree_i__0__1> rel_10_Reachable = mk<t_btree_i__0__1>();
souffle::RelationWrapper<t_btree_i__0__1> wrapper_rel_10_Reachable;
// -- Table: ReachableNullAt
Own<t_btree_iiiiiii__0_1_2_3_4_5_6__1111111> rel_11_ReachableNullAt = mk<t_btree_iiiiiii__0_1_2_3_4_5_6__1111111>();
souffle::RelationWrapper<t_btree_iiiiiii__0_1_2_3_4_5_6__1111111> wrapper_rel_11_ReachableNullAt;
// -- Table: ReachableNullAtLine
Own<t_btree_iiiiiiiii__0_1_2_3_4_5_6_7_8__111111111> rel_12_ReachableNullAtLine = mk<t_btree_iiiiiiiii__0_1_2_3_4_5_6_7_8__111111111>();
souffle::RelationWrapper<t_btree_iiiiiiiii__0_1_2_3_4_5_6_7_8__111111111> wrapper_rel_12_ReachableNullAtLine;
public:
Sf_small_transformed()
: wrapper_rel_1_InstructionLine(0, *rel_1_InstructionLine, *this, "InstructionLine", std::array<const char *,4>{{"s:symbol","s:symbol","s:symbol","s:symbol"}}, std::array<const char *,4>{{"v0","v1","v2","v3"}}, 0)
, wrapper_rel_2_LoadArrayIndex(1, *rel_2_LoadArrayIndex, *this, "LoadArrayIndex", std::array<const char *,5>{{"s:symbol","s:symbol","s:symbol","s:symbol","s:symbol"}}, std::array<const char *,5>{{"v0","v1","v2","v3","v4"}}, 0)
, wrapper_rel_3_symlog_domain_symlog_symbolic_0(2, *rel_3_symlog_domain_symlog_symbolic_0, *this, "symlog_domain_symlog_symbolic_0", std::array<const char *,1>{{"s:symbol"}}, std::array<const char *,1>{{"v0"}}, 0)
, wrapper_rel_4_symlog_domain_symlog_symbolic_1(3, *rel_4_symlog_domain_symlog_symbolic_1, *this, "symlog_domain_symlog_symbolic_1", std::array<const char *,1>{{"s:symbol"}}, std::array<const char *,1>{{"v0"}}, 0)
, wrapper_rel_5_symlog_domain_symlog_symbolic_2(4, *rel_5_symlog_domain_symlog_symbolic_2, *this, "symlog_domain_symlog_symbolic_2", std::array<const char *,1>{{"s:symbol"}}, std::array<const char *,1>{{"v0"}}, 0)
, wrapper_rel_6_symlog_domain_symlog_symbolic_3(5, *rel_6_symlog_domain_symlog_symbolic_3, *this, "symlog_domain_symlog_symbolic_3", std::array<const char *,1>{{"s:symbol"}}, std::array<const char *,1>{{"v0"}}, 0)
, wrapper_rel_7_VarPointsTo(6, *rel_7_VarPointsTo, *this, "VarPointsTo", std::array<const char *,8>{{"s:symbol","s:symbol","s:symbol","s:symbol","s:symbol","s:symbol","s:symbol","s:symbol"}}, std::array<const char *,8>{{"v0","v1","v2","v3","v4","v5","v6","v7"}}, 0)
, wrapper_rel_8_VarPointsToNull(7, *rel_8_VarPointsToNull, *this, "VarPointsToNull", std::array<const char *,5>{{"s:symbol","s:symbol","s:symbol","s:symbol","s:symbol"}}, std::array<const char *,5>{{"v0","v1","v2","v3","v4"}}, 0)
, wrapper_rel_9_NullAt(8, *rel_9_NullAt, *this, "NullAt", std::array<const char *,7>{{"s:symbol","s:symbol","s:symbol","s:symbol","s:symbol","s:symbol","s:symbol"}}, std::array<const char *,7>{{"v0","v1","v2","v3","v4","v5","v6"}}, 0)
, wrapper_rel_10_Reachable(9, *rel_10_Reachable, *this, "Reachable", std::array<const char *,1>{{"s:symbol"}}, std::array<const char *,1>{{"v0"}}, 0)
, wrapper_rel_11_ReachableNullAt(10, *rel_11_ReachableNullAt, *this, "ReachableNullAt", std::array<const char *,7>{{"s:symbol","s:symbol","s:symbol","s:symbol","s:symbol","s:symbol","s:symbol"}}, std::array<const char *,7>{{"v0","v1","v2","v3","v4","v5","v6"}}, 0)
, wrapper_rel_12_ReachableNullAtLine(11, *rel_12_ReachableNullAtLine, *this, "ReachableNullAtLine", std::array<const char *,9>{{"s:symbol","s:symbol","s:symbol","s:symbol","s:symbol","s:symbol","s:symbol","s:symbol","s:symbol"}}, std::array<const char *,9>{{"v0","v1","v2","v3","v4","v5","v6","v7","v8"}}, 0)
{
addRelation("InstructionLine", wrapper_rel_1_InstructionLine, false, false);
addRelation("LoadArrayIndex", wrapper_rel_2_LoadArrayIndex, false, false);
addRelation("symlog_domain_symlog_symbolic_0", wrapper_rel_3_symlog_domain_symlog_symbolic_0, false, false);
addRelation("symlog_domain_symlog_symbolic_1", wrapper_rel_4_symlog_domain_symlog_symbolic_1, false, false);
addRelation("symlog_domain_symlog_symbolic_2", wrapper_rel_5_symlog_domain_symlog_symbolic_2, false, false);
addRelation("symlog_domain_symlog_symbolic_3", wrapper_rel_6_symlog_domain_symlog_symbolic_3, false, false);
addRelation("VarPointsTo", wrapper_rel_7_VarPointsTo, false, false);
addRelation("VarPointsToNull", wrapper_rel_8_VarPointsToNull, false, false);
addRelation("NullAt", wrapper_rel_9_NullAt, false, false);
addRelation("Reachable", wrapper_rel_10_Reachable, false, false);
addRelation("ReachableNullAt", wrapper_rel_11_ReachableNullAt, false, false);
addRelation("ReachableNullAtLine", wrapper_rel_12_ReachableNullAtLine, false, true);
}
~Sf_small_transformed() {
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
{
 std::vector<RamDomain> args, ret;
subroutine_8(args, ret);
}
{
 std::vector<RamDomain> args, ret;
subroutine_9(args, ret);
}
{
 std::vector<RamDomain> args, ret;
subroutine_10(args, ret);
}
{
 std::vector<RamDomain> args, ret;
subroutine_11(args, ret);
}
{
 std::vector<RamDomain> args, ret;
subroutine_2(args, ret);
}
{
 std::vector<RamDomain> args, ret;
subroutine_3(args, ret);
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
try {std::map<std::string, std::string> directiveMap({{"IO","file"},{"attributeNames","v0\tv1\tv2\tv3\tv4\tv5\tv6\tv7\tv8"},{"auxArity","0"},{"name","ReachableNullAtLine"},{"operation","output"},{"output-dir","."},{"params","{\"records\": {}, \"relation\": {\"arity\": 9, \"params\": [\"v0\", \"v1\", \"v2\", \"v3\", \"v4\", \"v5\", \"v6\", \"v7\", \"v8\"]}}"},{"types","{\"ADTs\": {}, \"records\": {}, \"relation\": {\"arity\": 9, \"types\": [\"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\"]}}"}});
if (!outputDirectoryArg.empty()) {directiveMap["output-dir"] = outputDirectoryArg;}
IOSystem::getInstance().getWriter(directiveMap, symTable, recordTable)->writeAll(*rel_12_ReachableNullAtLine);
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
rwOperation["types"] = "{\"relation\": {\"arity\": 9, \"auxArity\": 0, \"types\": [\"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\"]}}";
IOSystem::getInstance().getWriter(rwOperation, symTable, recordTable)->writeAll(*rel_12_ReachableNullAtLine);
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
if (name == "stratum_10") {
subroutine_2(args, ret);
return;}
if (name == "stratum_11") {
subroutine_3(args, ret);
return;}
if (name == "stratum_2") {
subroutine_4(args, ret);
return;}
if (name == "stratum_3") {
subroutine_5(args, ret);
return;}
if (name == "stratum_4") {
subroutine_6(args, ret);
return;}
if (name == "stratum_5") {
subroutine_7(args, ret);
return;}
if (name == "stratum_6") {
subroutine_8(args, ret);
return;}
if (name == "stratum_7") {
subroutine_9(args, ret);
return;}
if (name == "stratum_8") {
subroutine_10(args, ret);
return;}
if (name == "stratum_9") {
subroutine_11(args, ret);
return;}
fatal("unknown subroutine");
}
#ifdef _MSC_VER
#pragma warning(disable: 4100)
#endif // _MSC_VER
void subroutine_0(const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) {
signalHandler->setMsg(R"_(InstructionLine("<ArrayNullLoad: void <init>()>","1","-1","ArrayNullLoad.java").
in file small_transformed_program.dl [23:1-23:84])_");
[&](){
CREATE_OP_CONTEXT(rel_1_InstructionLine_op_ctxt,rel_1_InstructionLine->createContext());
Tuple<RamDomain,4> tuple{{ramBitCast(RamSigned(0)),ramBitCast(RamSigned(1)),ramBitCast(RamSigned(2)),ramBitCast(RamSigned(3))}};
rel_1_InstructionLine->insert(tuple,READ_OP_CONTEXT(rel_1_InstructionLine_op_ctxt));
}
();signalHandler->setMsg(R"_(InstructionLine("<ArrayNullLoad: void <init>()>","2","1","ArrayNullLoad.java").
in file small_transformed_program.dl [24:1-24:83])_");
[&](){
CREATE_OP_CONTEXT(rel_1_InstructionLine_op_ctxt,rel_1_InstructionLine->createContext());
Tuple<RamDomain,4> tuple{{ramBitCast(RamSigned(0)),ramBitCast(RamSigned(4)),ramBitCast(RamSigned(1)),ramBitCast(RamSigned(3))}};
rel_1_InstructionLine->insert(tuple,READ_OP_CONTEXT(rel_1_InstructionLine_op_ctxt));
}
();signalHandler->setMsg(R"_(InstructionLine("<ArrayNullLoad: void <init>()>","3","1","ArrayNullLoad.java").
in file small_transformed_program.dl [25:1-25:83])_");
[&](){
CREATE_OP_CONTEXT(rel_1_InstructionLine_op_ctxt,rel_1_InstructionLine->createContext());
Tuple<RamDomain,4> tuple{{ramBitCast(RamSigned(0)),ramBitCast(RamSigned(5)),ramBitCast(RamSigned(1)),ramBitCast(RamSigned(3))}};
rel_1_InstructionLine->insert(tuple,READ_OP_CONTEXT(rel_1_InstructionLine_op_ctxt));
}
();signalHandler->setMsg(R"_(InstructionLine("<ArrayNullLoad: void main(java.lang.String[])>","1","-1","ArrayNullLoad.java").
in file small_transformed_program.dl [26:1-26:100])_");
[&](){
CREATE_OP_CONTEXT(rel_1_InstructionLine_op_ctxt,rel_1_InstructionLine->createContext());
Tuple<RamDomain,4> tuple{{ramBitCast(RamSigned(6)),ramBitCast(RamSigned(1)),ramBitCast(RamSigned(2)),ramBitCast(RamSigned(3))}};
rel_1_InstructionLine->insert(tuple,READ_OP_CONTEXT(rel_1_InstructionLine_op_ctxt));
}
();signalHandler->setMsg(R"_(InstructionLine("<ArrayNullLoad: void main(java.lang.String[])>","2","3","ArrayNullLoad.java").
in file small_transformed_program.dl [27:1-27:99])_");
[&](){
CREATE_OP_CONTEXT(rel_1_InstructionLine_op_ctxt,rel_1_InstructionLine->createContext());
Tuple<RamDomain,4> tuple{{ramBitCast(RamSigned(6)),ramBitCast(RamSigned(4)),ramBitCast(RamSigned(5)),ramBitCast(RamSigned(3))}};
rel_1_InstructionLine->insert(tuple,READ_OP_CONTEXT(rel_1_InstructionLine_op_ctxt));
}
();signalHandler->setMsg(R"_(InstructionLine("<ArrayNullLoad: void main(java.lang.String[])>","3","4","ArrayNullLoad.java").
in file small_transformed_program.dl [28:1-28:99])_");
[&](){
CREATE_OP_CONTEXT(rel_1_InstructionLine_op_ctxt,rel_1_InstructionLine->createContext());
Tuple<RamDomain,4> tuple{{ramBitCast(RamSigned(6)),ramBitCast(RamSigned(5)),ramBitCast(RamSigned(7)),ramBitCast(RamSigned(3))}};
rel_1_InstructionLine->insert(tuple,READ_OP_CONTEXT(rel_1_InstructionLine_op_ctxt));
}
();signalHandler->setMsg(R"_(InstructionLine("<ArrayNullLoad: void main(java.lang.String[])>","4","4","ArrayNullLoad.java").
in file small_transformed_program.dl [29:1-29:99])_");
[&](){
CREATE_OP_CONTEXT(rel_1_InstructionLine_op_ctxt,rel_1_InstructionLine->createContext());
Tuple<RamDomain,4> tuple{{ramBitCast(RamSigned(6)),ramBitCast(RamSigned(7)),ramBitCast(RamSigned(7)),ramBitCast(RamSigned(3))}};
rel_1_InstructionLine->insert(tuple,READ_OP_CONTEXT(rel_1_InstructionLine_op_ctxt));
}
();signalHandler->setMsg(R"_(InstructionLine("<ArrayNullLoad: void main(java.lang.String[])>","5","5","ArrayNullLoad.java").
in file small_transformed_program.dl [30:1-30:99])_");
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
in file small_transformed_program.dl [22:1-22:255])_");
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
signalHandler->setMsg(R"_(ReachableNullAt(meth,index,type,symlog_binding_symlog_symbolic_0,symlog_binding_symlog_symbolic_1,symlog_binding_symlog_symbolic_2,symlog_binding_symlog_symbolic_3) :- 
   NullAt(meth,index,type,symlog_binding_symlog_symbolic_0,symlog_binding_symlog_symbolic_1,symlog_binding_symlog_symbolic_2,symlog_binding_symlog_symbolic_3),
   Reachable(meth),
   symlog_domain_symlog_symbolic_0(symlog_binding_symlog_symbolic_0),
   symlog_domain_symlog_symbolic_1(symlog_binding_symlog_symbolic_1),
   symlog_domain_symlog_symbolic_2(symlog_binding_symlog_symbolic_2),
   symlog_domain_symlog_symbolic_3(symlog_binding_symlog_symbolic_3).
in file small_transformed_program.dl [18:1-18:622])_");
if(!(rel_10_Reachable->empty()) && !(rel_5_symlog_domain_symlog_symbolic_2->empty()) && !(rel_3_symlog_domain_symlog_symbolic_0->empty()) && !(rel_4_symlog_domain_symlog_symbolic_1->empty()) && !(rel_9_NullAt->empty()) && !(rel_6_symlog_domain_symlog_symbolic_3->empty())) {
[&](){
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
CREATE_OP_CONTEXT(rel_10_Reachable_op_ctxt,rel_10_Reachable->createContext());
CREATE_OP_CONTEXT(rel_11_ReachableNullAt_op_ctxt,rel_11_ReachableNullAt->createContext());
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
CREATE_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt,rel_4_symlog_domain_symlog_symbolic_1->createContext());
CREATE_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt,rel_3_symlog_domain_symlog_symbolic_0->createContext());
CREATE_OP_CONTEXT(rel_9_NullAt_op_ctxt,rel_9_NullAt->createContext());
for(const auto& env0 : *rel_9_NullAt) {
if( rel_6_symlog_domain_symlog_symbolic_3->contains(Tuple<RamDomain,1>{{ramBitCast(env0[6])}},READ_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt)) && rel_3_symlog_domain_symlog_symbolic_0->contains(Tuple<RamDomain,1>{{ramBitCast(env0[3])}},READ_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt)) && rel_4_symlog_domain_symlog_symbolic_1->contains(Tuple<RamDomain,1>{{ramBitCast(env0[4])}},READ_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt)) && rel_5_symlog_domain_symlog_symbolic_2->contains(Tuple<RamDomain,1>{{ramBitCast(env0[5])}},READ_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt)) && rel_10_Reachable->contains(Tuple<RamDomain,1>{{ramBitCast(env0[0])}},READ_OP_CONTEXT(rel_10_Reachable_op_ctxt))) {
Tuple<RamDomain,7> tuple{{ramBitCast(env0[0]),ramBitCast(env0[1]),ramBitCast(env0[2]),ramBitCast(env0[3]),ramBitCast(env0[4]),ramBitCast(env0[5]),ramBitCast(env0[6])}};
rel_11_ReachableNullAt->insert(tuple,READ_OP_CONTEXT(rel_11_ReachableNullAt_op_ctxt));
}
}
}
();}
if (pruneImdtRels) rel_10_Reachable->purge();
if (pruneImdtRels) rel_9_NullAt->purge();
}
#ifdef _MSC_VER
#pragma warning(default: 4100)
#endif // _MSC_VER
#ifdef _MSC_VER
#pragma warning(disable: 4100)
#endif // _MSC_VER
void subroutine_3(const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) {
signalHandler->setMsg(R"_(ReachableNullAtLine(meth,index,file,line,type,symlog_binding_symlog_symbolic_0,symlog_binding_symlog_symbolic_1,symlog_binding_symlog_symbolic_2,symlog_binding_symlog_symbolic_3) :- 
   ReachableNullAt(meth,index,type,symlog_binding_symlog_symbolic_0,symlog_binding_symlog_symbolic_1,symlog_binding_symlog_symbolic_2,symlog_binding_symlog_symbolic_3),
   InstructionLine(meth,index,line,file),
   symlog_domain_symlog_symbolic_0(symlog_binding_symlog_symbolic_0),
   symlog_domain_symlog_symbolic_1(symlog_binding_symlog_symbolic_1),
   symlog_domain_symlog_symbolic_2(symlog_binding_symlog_symbolic_2),
   symlog_domain_symlog_symbolic_3(symlog_binding_symlog_symbolic_3).
in file small_transformed_program.dl [19:1-19:672])_");
if(!(rel_3_symlog_domain_symlog_symbolic_0->empty()) && !(rel_6_symlog_domain_symlog_symbolic_3->empty()) && !(rel_4_symlog_domain_symlog_symbolic_1->empty()) && !(rel_5_symlog_domain_symlog_symbolic_2->empty()) && !(rel_11_ReachableNullAt->empty()) && !(rel_1_InstructionLine->empty())) {
[&](){
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
CREATE_OP_CONTEXT(rel_12_ReachableNullAtLine_op_ctxt,rel_12_ReachableNullAtLine->createContext());
CREATE_OP_CONTEXT(rel_11_ReachableNullAt_op_ctxt,rel_11_ReachableNullAt->createContext());
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
CREATE_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt,rel_4_symlog_domain_symlog_symbolic_1->createContext());
CREATE_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt,rel_3_symlog_domain_symlog_symbolic_0->createContext());
CREATE_OP_CONTEXT(rel_1_InstructionLine_op_ctxt,rel_1_InstructionLine->createContext());
for(const auto& env0 : *rel_11_ReachableNullAt) {
if( rel_4_symlog_domain_symlog_symbolic_1->contains(Tuple<RamDomain,1>{{ramBitCast(env0[4])}},READ_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt)) && rel_6_symlog_domain_symlog_symbolic_3->contains(Tuple<RamDomain,1>{{ramBitCast(env0[6])}},READ_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt)) && rel_5_symlog_domain_symlog_symbolic_2->contains(Tuple<RamDomain,1>{{ramBitCast(env0[5])}},READ_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt)) && rel_3_symlog_domain_symlog_symbolic_0->contains(Tuple<RamDomain,1>{{ramBitCast(env0[3])}},READ_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt))) {
auto range = rel_1_InstructionLine->lowerUpperRange_1100(Tuple<RamDomain,4>{{ramBitCast(env0[0]), ramBitCast(env0[1]), ramBitCast<RamDomain>(MIN_RAM_SIGNED), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,4>{{ramBitCast(env0[0]), ramBitCast(env0[1]), ramBitCast<RamDomain>(MAX_RAM_SIGNED), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_1_InstructionLine_op_ctxt));
for(const auto& env1 : range) {
Tuple<RamDomain,9> tuple{{ramBitCast(env0[0]),ramBitCast(env0[1]),ramBitCast(env1[3]),ramBitCast(env1[2]),ramBitCast(env0[2]),ramBitCast(env0[3]),ramBitCast(env0[4]),ramBitCast(env0[5]),ramBitCast(env0[6])}};
rel_12_ReachableNullAtLine->insert(tuple,READ_OP_CONTEXT(rel_12_ReachableNullAtLine_op_ctxt));
}
}
}
}
();}
if (performIO) {
try {std::map<std::string, std::string> directiveMap({{"IO","file"},{"attributeNames","v0\tv1\tv2\tv3\tv4\tv5\tv6\tv7\tv8"},{"auxArity","0"},{"name","ReachableNullAtLine"},{"operation","output"},{"output-dir","."},{"params","{\"records\": {}, \"relation\": {\"arity\": 9, \"params\": [\"v0\", \"v1\", \"v2\", \"v3\", \"v4\", \"v5\", \"v6\", \"v7\", \"v8\"]}}"},{"types","{\"ADTs\": {}, \"records\": {}, \"relation\": {\"arity\": 9, \"types\": [\"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\", \"s:symbol\"]}}"}});
if (!outputDirectory.empty()) {directiveMap["output-dir"] = outputDirectory;}
IOSystem::getInstance().getWriter(directiveMap, symTable, recordTable)->writeAll(*rel_12_ReachableNullAtLine);
} catch (std::exception& e) {std::cerr << e.what();exit(1);}
}
if (pruneImdtRels) rel_1_InstructionLine->purge();
if (pruneImdtRels) rel_11_ReachableNullAt->purge();
if (pruneImdtRels) rel_3_symlog_domain_symlog_symbolic_0->purge();
if (pruneImdtRels) rel_4_symlog_domain_symlog_symbolic_1->purge();
if (pruneImdtRels) rel_5_symlog_domain_symlog_symbolic_2->purge();
if (pruneImdtRels) rel_6_symlog_domain_symlog_symbolic_3->purge();
}
#ifdef _MSC_VER
#pragma warning(default: 4100)
#endif // _MSC_VER
#ifdef _MSC_VER
#pragma warning(disable: 4100)
#endif // _MSC_VER
void subroutine_4(const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) {
signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_0("<<unique-hcontext>>").
in file small_transformed_program.dl [36:1-36:56])_");
[&](){
CREATE_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt,rel_3_symlog_domain_symlog_symbolic_0->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(12))}};
rel_3_symlog_domain_symlog_symbolic_0->insert(tuple,READ_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_0("[symlog_symbolic_0, symlog_symbolic_1, symlog_symbolic_2, symlog_symbolic_3],  eq/neq ").
in file small_transformed_program.dl [48:1-48:123])_");
[&](){
CREATE_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt,rel_3_symlog_domain_symlog_symbolic_0->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(13))}};
rel_3_symlog_domain_symlog_symbolic_0->insert(tuple,READ_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_0("[symlog_symbolic_0, symlog_symbolic_1, symlog_symbolic_2],  eq/neq , [symlog_symbolic_3]").
in file small_transformed_program.dl [49:1-49:125])_");
[&](){
CREATE_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt,rel_3_symlog_domain_symlog_symbolic_0->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(14))}};
rel_3_symlog_domain_symlog_symbolic_0->insert(tuple,READ_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_0("[symlog_symbolic_0, symlog_symbolic_1, symlog_symbolic_3],  eq/neq , [symlog_symbolic_2]").
in file small_transformed_program.dl [50:1-50:125])_");
[&](){
CREATE_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt,rel_3_symlog_domain_symlog_symbolic_0->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(15))}};
rel_3_symlog_domain_symlog_symbolic_0->insert(tuple,READ_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_0("[symlog_symbolic_0, symlog_symbolic_1],  eq/neq , [symlog_symbolic_2, symlog_symbolic_3]").
in file small_transformed_program.dl [51:1-51:125])_");
[&](){
CREATE_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt,rel_3_symlog_domain_symlog_symbolic_0->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(16))}};
rel_3_symlog_domain_symlog_symbolic_0->insert(tuple,READ_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_0("[symlog_symbolic_0, symlog_symbolic_2, symlog_symbolic_3],  eq/neq , [symlog_symbolic_1]").
in file small_transformed_program.dl [52:1-52:125])_");
[&](){
CREATE_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt,rel_3_symlog_domain_symlog_symbolic_0->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(17))}};
rel_3_symlog_domain_symlog_symbolic_0->insert(tuple,READ_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_0("[symlog_symbolic_0, symlog_symbolic_2],  eq/neq , [symlog_symbolic_1, symlog_symbolic_3]").
in file small_transformed_program.dl [53:1-53:125])_");
[&](){
CREATE_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt,rel_3_symlog_domain_symlog_symbolic_0->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(18))}};
rel_3_symlog_domain_symlog_symbolic_0->insert(tuple,READ_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_0("[symlog_symbolic_0, symlog_symbolic_3],  eq/neq , [symlog_symbolic_1, symlog_symbolic_2]").
in file small_transformed_program.dl [54:1-54:125])_");
[&](){
CREATE_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt,rel_3_symlog_domain_symlog_symbolic_0->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(19))}};
rel_3_symlog_domain_symlog_symbolic_0->insert(tuple,READ_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_0("[symlog_symbolic_0],  eq/neq , [symlog_symbolic_1, symlog_symbolic_2, symlog_symbolic_3]").
in file small_transformed_program.dl [55:1-55:125])_");
[&](){
CREATE_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt,rel_3_symlog_domain_symlog_symbolic_0->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(20))}};
rel_3_symlog_domain_symlog_symbolic_0->insert(tuple,READ_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt));
}
();}
#ifdef _MSC_VER
#pragma warning(default: 4100)
#endif // _MSC_VER
#ifdef _MSC_VER
#pragma warning(disable: 4100)
#endif // _MSC_VER
void subroutine_5(const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) {
signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_1("<<main method array>>").
in file small_transformed_program.dl [37:1-37:58])_");
[&](){
CREATE_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt,rel_4_symlog_domain_symlog_symbolic_1->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(21))}};
rel_4_symlog_domain_symlog_symbolic_1->insert(tuple,READ_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_1("<<null pseudo heap>>").
in file small_transformed_program.dl [45:1-45:57])_");
[&](){
CREATE_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt,rel_4_symlog_domain_symlog_symbolic_1->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(22))}};
rel_4_symlog_domain_symlog_symbolic_1->insert(tuple,READ_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_1("[symlog_symbolic_0, symlog_symbolic_1, symlog_symbolic_2, symlog_symbolic_3],  eq/neq ").
in file small_transformed_program.dl [56:1-56:123])_");
[&](){
CREATE_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt,rel_4_symlog_domain_symlog_symbolic_1->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(13))}};
rel_4_symlog_domain_symlog_symbolic_1->insert(tuple,READ_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_1("[symlog_symbolic_0, symlog_symbolic_1, symlog_symbolic_2],  eq/neq , [symlog_symbolic_3]").
in file small_transformed_program.dl [57:1-57:125])_");
[&](){
CREATE_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt,rel_4_symlog_domain_symlog_symbolic_1->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(14))}};
rel_4_symlog_domain_symlog_symbolic_1->insert(tuple,READ_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_1("[symlog_symbolic_0, symlog_symbolic_1, symlog_symbolic_3],  eq/neq , [symlog_symbolic_2]").
in file small_transformed_program.dl [58:1-58:125])_");
[&](){
CREATE_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt,rel_4_symlog_domain_symlog_symbolic_1->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(15))}};
rel_4_symlog_domain_symlog_symbolic_1->insert(tuple,READ_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_1("[symlog_symbolic_0, symlog_symbolic_1],  eq/neq , [symlog_symbolic_2, symlog_symbolic_3]").
in file small_transformed_program.dl [59:1-59:125])_");
[&](){
CREATE_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt,rel_4_symlog_domain_symlog_symbolic_1->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(16))}};
rel_4_symlog_domain_symlog_symbolic_1->insert(tuple,READ_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_1("[symlog_symbolic_1],  eq/neq , [symlog_symbolic_0, symlog_symbolic_2, symlog_symbolic_3]").
in file small_transformed_program.dl [60:1-60:125])_");
[&](){
CREATE_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt,rel_4_symlog_domain_symlog_symbolic_1->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(23))}};
rel_4_symlog_domain_symlog_symbolic_1->insert(tuple,READ_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_1("[symlog_symbolic_1, symlog_symbolic_3],  eq/neq , [symlog_symbolic_0, symlog_symbolic_2]").
in file small_transformed_program.dl [61:1-61:125])_");
[&](){
CREATE_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt,rel_4_symlog_domain_symlog_symbolic_1->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(24))}};
rel_4_symlog_domain_symlog_symbolic_1->insert(tuple,READ_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_1("[symlog_symbolic_1, symlog_symbolic_2],  eq/neq , [symlog_symbolic_0, symlog_symbolic_3]").
in file small_transformed_program.dl [62:1-62:125])_");
[&](){
CREATE_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt,rel_4_symlog_domain_symlog_symbolic_1->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(25))}};
rel_4_symlog_domain_symlog_symbolic_1->insert(tuple,READ_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_1("[symlog_symbolic_1, symlog_symbolic_2, symlog_symbolic_3],  eq/neq , [symlog_symbolic_0]").
in file small_transformed_program.dl [63:1-63:125])_");
[&](){
CREATE_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt,rel_4_symlog_domain_symlog_symbolic_1->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(26))}};
rel_4_symlog_domain_symlog_symbolic_1->insert(tuple,READ_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt));
}
();}
#ifdef _MSC_VER
#pragma warning(default: 4100)
#endif // _MSC_VER
#ifdef _MSC_VER
#pragma warning(disable: 4100)
#endif // _MSC_VER
void subroutine_6(const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) {
signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_2("4").
in file small_transformed_program.dl [38:1-38:38])_");
[&](){
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(7))}};
rel_5_symlog_domain_symlog_symbolic_2->insert(tuple,READ_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_2("[symlog_symbolic_0, symlog_symbolic_1, symlog_symbolic_2, symlog_symbolic_3],  eq/neq ").
in file small_transformed_program.dl [64:1-64:123])_");
[&](){
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(13))}};
rel_5_symlog_domain_symlog_symbolic_2->insert(tuple,READ_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_2("[symlog_symbolic_0, symlog_symbolic_1, symlog_symbolic_2],  eq/neq , [symlog_symbolic_3]").
in file small_transformed_program.dl [65:1-65:125])_");
[&](){
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(14))}};
rel_5_symlog_domain_symlog_symbolic_2->insert(tuple,READ_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_2("[symlog_symbolic_2],  eq/neq , [symlog_symbolic_0, symlog_symbolic_1, symlog_symbolic_3]").
in file small_transformed_program.dl [66:1-66:125])_");
[&](){
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(27))}};
rel_5_symlog_domain_symlog_symbolic_2->insert(tuple,READ_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_2("[symlog_symbolic_2, symlog_symbolic_3],  eq/neq , [symlog_symbolic_0, symlog_symbolic_1]").
in file small_transformed_program.dl [67:1-67:125])_");
[&](){
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(28))}};
rel_5_symlog_domain_symlog_symbolic_2->insert(tuple,READ_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_2("[symlog_symbolic_0, symlog_symbolic_2, symlog_symbolic_3],  eq/neq , [symlog_symbolic_1]").
in file small_transformed_program.dl [68:1-68:125])_");
[&](){
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(17))}};
rel_5_symlog_domain_symlog_symbolic_2->insert(tuple,READ_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_2("[symlog_symbolic_0, symlog_symbolic_2],  eq/neq , [symlog_symbolic_1, symlog_symbolic_3]").
in file small_transformed_program.dl [69:1-69:125])_");
[&](){
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(18))}};
rel_5_symlog_domain_symlog_symbolic_2->insert(tuple,READ_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_2("[symlog_symbolic_1, symlog_symbolic_2],  eq/neq , [symlog_symbolic_0, symlog_symbolic_3]").
in file small_transformed_program.dl [70:1-70:125])_");
[&](){
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(25))}};
rel_5_symlog_domain_symlog_symbolic_2->insert(tuple,READ_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_2("[symlog_symbolic_1, symlog_symbolic_2, symlog_symbolic_3],  eq/neq , [symlog_symbolic_0]").
in file small_transformed_program.dl [71:1-71:125])_");
[&](){
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(26))}};
rel_5_symlog_domain_symlog_symbolic_2->insert(tuple,READ_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_2("symlog_symbolic_0").
in file small_transformed_program.dl [80:1-80:54])_");
[&](){
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(29))}};
rel_5_symlog_domain_symlog_symbolic_2->insert(tuple,READ_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_2("<<unique-hcontext>>").
in file small_transformed_program.dl [81:1-81:56])_");
[&](){
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(12))}};
rel_5_symlog_domain_symlog_symbolic_2->insert(tuple,READ_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt));
}
();}
#ifdef _MSC_VER
#pragma warning(default: 4100)
#endif // _MSC_VER
#ifdef _MSC_VER
#pragma warning(disable: 4100)
#endif // _MSC_VER
void subroutine_7(const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) {
signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_3("<ArrayNullLoad: void main(java.lang.String[])>/@parameter0").
in file small_transformed_program.dl [39:1-39:95])_");
[&](){
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(30))}};
rel_6_symlog_domain_symlog_symbolic_3->insert(tuple,READ_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_3("<ArrayNullLoad: void main(java.lang.String[])>/args#_0").
in file small_transformed_program.dl [43:1-43:91])_");
[&](){
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(31))}};
rel_6_symlog_domain_symlog_symbolic_3->insert(tuple,READ_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_3("<ArrayNullLoad: void main(java.lang.String[])>/array#_3").
in file small_transformed_program.dl [47:1-47:92])_");
[&](){
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(11))}};
rel_6_symlog_domain_symlog_symbolic_3->insert(tuple,READ_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_3("[symlog_symbolic_0, symlog_symbolic_1, symlog_symbolic_2, symlog_symbolic_3],  eq/neq ").
in file small_transformed_program.dl [72:1-72:123])_");
[&](){
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(13))}};
rel_6_symlog_domain_symlog_symbolic_3->insert(tuple,READ_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_3("[symlog_symbolic_3],  eq/neq , [symlog_symbolic_0, symlog_symbolic_1, symlog_symbolic_2]").
in file small_transformed_program.dl [73:1-73:125])_");
[&](){
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(32))}};
rel_6_symlog_domain_symlog_symbolic_3->insert(tuple,READ_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_3("[symlog_symbolic_0, symlog_symbolic_1, symlog_symbolic_3],  eq/neq , [symlog_symbolic_2]").
in file small_transformed_program.dl [74:1-74:125])_");
[&](){
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(15))}};
rel_6_symlog_domain_symlog_symbolic_3->insert(tuple,READ_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_3("[symlog_symbolic_2, symlog_symbolic_3],  eq/neq , [symlog_symbolic_0, symlog_symbolic_1]").
in file small_transformed_program.dl [75:1-75:125])_");
[&](){
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(28))}};
rel_6_symlog_domain_symlog_symbolic_3->insert(tuple,READ_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_3("[symlog_symbolic_0, symlog_symbolic_2, symlog_symbolic_3],  eq/neq , [symlog_symbolic_1]").
in file small_transformed_program.dl [76:1-76:125])_");
[&](){
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(17))}};
rel_6_symlog_domain_symlog_symbolic_3->insert(tuple,READ_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_3("[symlog_symbolic_1, symlog_symbolic_3],  eq/neq , [symlog_symbolic_0, symlog_symbolic_2]").
in file small_transformed_program.dl [77:1-77:125])_");
[&](){
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(24))}};
rel_6_symlog_domain_symlog_symbolic_3->insert(tuple,READ_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_3("[symlog_symbolic_0, symlog_symbolic_3],  eq/neq , [symlog_symbolic_1, symlog_symbolic_2]").
in file small_transformed_program.dl [78:1-78:125])_");
[&](){
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(19))}};
rel_6_symlog_domain_symlog_symbolic_3->insert(tuple,READ_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt));
}
();signalHandler->setMsg(R"_(symlog_domain_symlog_symbolic_3("[symlog_symbolic_1, symlog_symbolic_2, symlog_symbolic_3],  eq/neq , [symlog_symbolic_0]").
in file small_transformed_program.dl [79:1-79:125])_");
[&](){
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(26))}};
rel_6_symlog_domain_symlog_symbolic_3->insert(tuple,READ_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt));
}
();}
#ifdef _MSC_VER
#pragma warning(default: 4100)
#endif // _MSC_VER
#ifdef _MSC_VER
#pragma warning(disable: 4100)
#endif // _MSC_VER
void subroutine_8(const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) {
signalHandler->setMsg(R"_(VarPointsTo("<<unique-hcontext>>","<<main method array>>","4","<ArrayNullLoad: void main(java.lang.String[])>/@parameter0",symlog_binding_symlog_symbolic_0,symlog_binding_symlog_symbolic_1,symlog_binding_symlog_symbolic_2,symlog_binding_symlog_symbolic_3) :- 
   symlog_domain_symlog_symbolic_0(symlog_binding_symlog_symbolic_0),
   symlog_domain_symlog_symbolic_1(symlog_binding_symlog_symbolic_1),
   symlog_domain_symlog_symbolic_2(symlog_binding_symlog_symbolic_2),
   symlog_domain_symlog_symbolic_3(symlog_binding_symlog_symbolic_3).
in file small_transformed_program.dl [31:1-31:534])_");
if(!(rel_4_symlog_domain_symlog_symbolic_1->empty()) && !(rel_5_symlog_domain_symlog_symbolic_2->empty()) && !(rel_3_symlog_domain_symlog_symbolic_0->empty()) && !(rel_6_symlog_domain_symlog_symbolic_3->empty())) {
[&](){
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
CREATE_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt,rel_4_symlog_domain_symlog_symbolic_1->createContext());
CREATE_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt,rel_3_symlog_domain_symlog_symbolic_0->createContext());
CREATE_OP_CONTEXT(rel_7_VarPointsTo_op_ctxt,rel_7_VarPointsTo->createContext());
for(const auto& env0 : *rel_3_symlog_domain_symlog_symbolic_0) {
for(const auto& env1 : *rel_4_symlog_domain_symlog_symbolic_1) {
for(const auto& env2 : *rel_5_symlog_domain_symlog_symbolic_2) {
for(const auto& env3 : *rel_6_symlog_domain_symlog_symbolic_3) {
Tuple<RamDomain,8> tuple{{ramBitCast(RamSigned(12)),ramBitCast(RamSigned(21)),ramBitCast(RamSigned(7)),ramBitCast(RamSigned(30)),ramBitCast(env0[0]),ramBitCast(env1[0]),ramBitCast(env2[0]),ramBitCast(env3[0])}};
rel_7_VarPointsTo->insert(tuple,READ_OP_CONTEXT(rel_7_VarPointsTo_op_ctxt));
}
}
}
}
}
();}
signalHandler->setMsg(R"_(VarPointsTo("<<unique-hcontext>>","<<main method array>>","4","<ArrayNullLoad: void main(java.lang.String[])>/args#_0",symlog_binding_symlog_symbolic_0,symlog_binding_symlog_symbolic_1,symlog_binding_symlog_symbolic_2,symlog_binding_symlog_symbolic_3) :- 
   symlog_domain_symlog_symbolic_0(symlog_binding_symlog_symbolic_0),
   symlog_domain_symlog_symbolic_1(symlog_binding_symlog_symbolic_1),
   symlog_domain_symlog_symbolic_2(symlog_binding_symlog_symbolic_2),
   symlog_domain_symlog_symbolic_3(symlog_binding_symlog_symbolic_3).
in file small_transformed_program.dl [32:1-32:530])_");
if(!(rel_4_symlog_domain_symlog_symbolic_1->empty()) && !(rel_5_symlog_domain_symlog_symbolic_2->empty()) && !(rel_3_symlog_domain_symlog_symbolic_0->empty()) && !(rel_6_symlog_domain_symlog_symbolic_3->empty())) {
[&](){
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
CREATE_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt,rel_4_symlog_domain_symlog_symbolic_1->createContext());
CREATE_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt,rel_3_symlog_domain_symlog_symbolic_0->createContext());
CREATE_OP_CONTEXT(rel_7_VarPointsTo_op_ctxt,rel_7_VarPointsTo->createContext());
for(const auto& env0 : *rel_3_symlog_domain_symlog_symbolic_0) {
for(const auto& env1 : *rel_4_symlog_domain_symlog_symbolic_1) {
for(const auto& env2 : *rel_5_symlog_domain_symlog_symbolic_2) {
for(const auto& env3 : *rel_6_symlog_domain_symlog_symbolic_3) {
Tuple<RamDomain,8> tuple{{ramBitCast(RamSigned(12)),ramBitCast(RamSigned(21)),ramBitCast(RamSigned(7)),ramBitCast(RamSigned(31)),ramBitCast(env0[0]),ramBitCast(env1[0]),ramBitCast(env2[0]),ramBitCast(env3[0])}};
rel_7_VarPointsTo->insert(tuple,READ_OP_CONTEXT(rel_7_VarPointsTo_op_ctxt));
}
}
}
}
}
();}
signalHandler->setMsg(R"_(VarPointsTo("<<unique-hcontext>>","<<null pseudo heap>>","4","<ArrayNullLoad: void main(java.lang.String[])>/array#_3",symlog_binding_symlog_symbolic_0,symlog_binding_symlog_symbolic_1,symlog_binding_symlog_symbolic_2,symlog_binding_symlog_symbolic_3) :- 
   symlog_domain_symlog_symbolic_0(symlog_binding_symlog_symbolic_0),
   symlog_domain_symlog_symbolic_1(symlog_binding_symlog_symbolic_1),
   symlog_domain_symlog_symbolic_2(symlog_binding_symlog_symbolic_2),
   symlog_domain_symlog_symbolic_3(symlog_binding_symlog_symbolic_3).
in file small_transformed_program.dl [33:1-33:530])_");
if(!(rel_4_symlog_domain_symlog_symbolic_1->empty()) && !(rel_5_symlog_domain_symlog_symbolic_2->empty()) && !(rel_3_symlog_domain_symlog_symbolic_0->empty()) && !(rel_6_symlog_domain_symlog_symbolic_3->empty())) {
[&](){
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
CREATE_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt,rel_4_symlog_domain_symlog_symbolic_1->createContext());
CREATE_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt,rel_3_symlog_domain_symlog_symbolic_0->createContext());
CREATE_OP_CONTEXT(rel_7_VarPointsTo_op_ctxt,rel_7_VarPointsTo->createContext());
for(const auto& env0 : *rel_3_symlog_domain_symlog_symbolic_0) {
for(const auto& env1 : *rel_4_symlog_domain_symlog_symbolic_1) {
for(const auto& env2 : *rel_5_symlog_domain_symlog_symbolic_2) {
for(const auto& env3 : *rel_6_symlog_domain_symlog_symbolic_3) {
Tuple<RamDomain,8> tuple{{ramBitCast(RamSigned(12)),ramBitCast(RamSigned(22)),ramBitCast(RamSigned(7)),ramBitCast(RamSigned(11)),ramBitCast(env0[0]),ramBitCast(env1[0]),ramBitCast(env2[0]),ramBitCast(env3[0])}};
rel_7_VarPointsTo->insert(tuple,READ_OP_CONTEXT(rel_7_VarPointsTo_op_ctxt));
}
}
}
}
}
();}
signalHandler->setMsg(R"_(VarPointsTo(symlog_binding_symlog_symbolic_0,symlog_binding_symlog_symbolic_1,symlog_binding_symlog_symbolic_2,symlog_binding_symlog_symbolic_3,symlog_binding_symlog_symbolic_0,symlog_binding_symlog_symbolic_1,symlog_binding_symlog_symbolic_2,symlog_binding_symlog_symbolic_3) :- 
   symlog_domain_symlog_symbolic_0(symlog_binding_symlog_symbolic_0),
   symlog_domain_symlog_symbolic_1(symlog_binding_symlog_symbolic_1),
   symlog_domain_symlog_symbolic_2(symlog_binding_symlog_symbolic_2),
   symlog_domain_symlog_symbolic_3(symlog_binding_symlog_symbolic_3).
in file small_transformed_program.dl [34:1-34:555])_");
if(!(rel_4_symlog_domain_symlog_symbolic_1->empty()) && !(rel_5_symlog_domain_symlog_symbolic_2->empty()) && !(rel_3_symlog_domain_symlog_symbolic_0->empty()) && !(rel_6_symlog_domain_symlog_symbolic_3->empty())) {
[&](){
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
CREATE_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt,rel_4_symlog_domain_symlog_symbolic_1->createContext());
CREATE_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt,rel_3_symlog_domain_symlog_symbolic_0->createContext());
CREATE_OP_CONTEXT(rel_7_VarPointsTo_op_ctxt,rel_7_VarPointsTo->createContext());
for(const auto& env0 : *rel_3_symlog_domain_symlog_symbolic_0) {
for(const auto& env1 : *rel_4_symlog_domain_symlog_symbolic_1) {
for(const auto& env2 : *rel_5_symlog_domain_symlog_symbolic_2) {
for(const auto& env3 : *rel_6_symlog_domain_symlog_symbolic_3) {
Tuple<RamDomain,8> tuple{{ramBitCast(env0[0]),ramBitCast(env1[0]),ramBitCast(env2[0]),ramBitCast(env3[0]),ramBitCast(env0[0]),ramBitCast(env1[0]),ramBitCast(env2[0]),ramBitCast(env3[0])}};
rel_7_VarPointsTo->insert(tuple,READ_OP_CONTEXT(rel_7_VarPointsTo_op_ctxt));
}
}
}
}
}
();}
}
#ifdef _MSC_VER
#pragma warning(default: 4100)
#endif // _MSC_VER
#ifdef _MSC_VER
#pragma warning(disable: 4100)
#endif // _MSC_VER
void subroutine_9(const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) {
signalHandler->setMsg(R"_(VarPointsToNull(var,symlog_binding_symlog_symbolic_0,symlog_binding_symlog_symbolic_1,symlog_binding_symlog_symbolic_2,symlog_binding_symlog_symbolic_3) :- 
   VarPointsTo(_,"<<null pseudo heap>>",_,var,symlog_binding_symlog_symbolic_0,symlog_binding_symlog_symbolic_1,symlog_binding_symlog_symbolic_2,symlog_binding_symlog_symbolic_3),
   symlog_domain_symlog_symbolic_0(symlog_binding_symlog_symbolic_0),
   symlog_domain_symlog_symbolic_1(symlog_binding_symlog_symbolic_1),
   symlog_domain_symlog_symbolic_2(symlog_binding_symlog_symbolic_2),
   symlog_domain_symlog_symbolic_3(symlog_binding_symlog_symbolic_3).
in file small_transformed_program.dl [16:1-16:612])_");
if(!(rel_3_symlog_domain_symlog_symbolic_0->empty()) && !(rel_5_symlog_domain_symlog_symbolic_2->empty()) && !(rel_4_symlog_domain_symlog_symbolic_1->empty()) && !(rel_6_symlog_domain_symlog_symbolic_3->empty()) && !(rel_7_VarPointsTo->empty())) {
[&](){
CREATE_OP_CONTEXT(rel_8_VarPointsToNull_op_ctxt,rel_8_VarPointsToNull->createContext());
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
CREATE_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt,rel_4_symlog_domain_symlog_symbolic_1->createContext());
CREATE_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt,rel_3_symlog_domain_symlog_symbolic_0->createContext());
CREATE_OP_CONTEXT(rel_7_VarPointsTo_op_ctxt,rel_7_VarPointsTo->createContext());
auto range = rel_7_VarPointsTo->lowerUpperRange_01000000(Tuple<RamDomain,8>{{ramBitCast<RamDomain>(MIN_RAM_SIGNED), ramBitCast(RamSigned(22)), ramBitCast<RamDomain>(MIN_RAM_SIGNED), ramBitCast<RamDomain>(MIN_RAM_SIGNED), ramBitCast<RamDomain>(MIN_RAM_SIGNED), ramBitCast<RamDomain>(MIN_RAM_SIGNED), ramBitCast<RamDomain>(MIN_RAM_SIGNED), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,8>{{ramBitCast<RamDomain>(MAX_RAM_SIGNED), ramBitCast(RamSigned(22)), ramBitCast<RamDomain>(MAX_RAM_SIGNED), ramBitCast<RamDomain>(MAX_RAM_SIGNED), ramBitCast<RamDomain>(MAX_RAM_SIGNED), ramBitCast<RamDomain>(MAX_RAM_SIGNED), ramBitCast<RamDomain>(MAX_RAM_SIGNED), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_7_VarPointsTo_op_ctxt));
for(const auto& env0 : range) {
if( rel_4_symlog_domain_symlog_symbolic_1->contains(Tuple<RamDomain,1>{{ramBitCast(env0[5])}},READ_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt)) && rel_6_symlog_domain_symlog_symbolic_3->contains(Tuple<RamDomain,1>{{ramBitCast(env0[7])}},READ_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt)) && rel_5_symlog_domain_symlog_symbolic_2->contains(Tuple<RamDomain,1>{{ramBitCast(env0[6])}},READ_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt)) && rel_3_symlog_domain_symlog_symbolic_0->contains(Tuple<RamDomain,1>{{ramBitCast(env0[4])}},READ_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt))) {
Tuple<RamDomain,5> tuple{{ramBitCast(env0[3]),ramBitCast(env0[4]),ramBitCast(env0[5]),ramBitCast(env0[6]),ramBitCast(env0[7])}};
rel_8_VarPointsToNull->insert(tuple,READ_OP_CONTEXT(rel_8_VarPointsToNull_op_ctxt));
}
}
}
();}
if (pruneImdtRels) rel_7_VarPointsTo->purge();
}
#ifdef _MSC_VER
#pragma warning(default: 4100)
#endif // _MSC_VER
#ifdef _MSC_VER
#pragma warning(disable: 4100)
#endif // _MSC_VER
void subroutine_10(const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) {
signalHandler->setMsg(R"_(NullAt(meth,index,"Load Array Index",symlog_binding_symlog_symbolic_0,symlog_binding_symlog_symbolic_1,symlog_binding_symlog_symbolic_2,symlog_binding_symlog_symbolic_3) :- 
   VarPointsToNull(var,symlog_binding_symlog_symbolic_0,symlog_binding_symlog_symbolic_1,symlog_binding_symlog_symbolic_2,symlog_binding_symlog_symbolic_3),
   LoadArrayIndex(_,index,_,var,meth),
   symlog_domain_symlog_symbolic_0(symlog_binding_symlog_symbolic_0),
   symlog_domain_symlog_symbolic_1(symlog_binding_symlog_symbolic_1),
   symlog_domain_symlog_symbolic_2(symlog_binding_symlog_symbolic_2),
   symlog_domain_symlog_symbolic_3(symlog_binding_symlog_symbolic_3).
in file small_transformed_program.dl [17:1-17:645])_");
if(!(rel_3_symlog_domain_symlog_symbolic_0->empty()) && !(rel_6_symlog_domain_symlog_symbolic_3->empty()) && !(rel_4_symlog_domain_symlog_symbolic_1->empty()) && !(rel_5_symlog_domain_symlog_symbolic_2->empty()) && !(rel_8_VarPointsToNull->empty()) && !(rel_2_LoadArrayIndex->empty())) {
[&](){
CREATE_OP_CONTEXT(rel_8_VarPointsToNull_op_ctxt,rel_8_VarPointsToNull->createContext());
CREATE_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt,rel_6_symlog_domain_symlog_symbolic_3->createContext());
CREATE_OP_CONTEXT(rel_2_LoadArrayIndex_op_ctxt,rel_2_LoadArrayIndex->createContext());
CREATE_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt,rel_5_symlog_domain_symlog_symbolic_2->createContext());
CREATE_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt,rel_4_symlog_domain_symlog_symbolic_1->createContext());
CREATE_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt,rel_3_symlog_domain_symlog_symbolic_0->createContext());
CREATE_OP_CONTEXT(rel_9_NullAt_op_ctxt,rel_9_NullAt->createContext());
for(const auto& env0 : *rel_8_VarPointsToNull) {
if( rel_4_symlog_domain_symlog_symbolic_1->contains(Tuple<RamDomain,1>{{ramBitCast(env0[2])}},READ_OP_CONTEXT(rel_4_symlog_domain_symlog_symbolic_1_op_ctxt)) && rel_6_symlog_domain_symlog_symbolic_3->contains(Tuple<RamDomain,1>{{ramBitCast(env0[4])}},READ_OP_CONTEXT(rel_6_symlog_domain_symlog_symbolic_3_op_ctxt)) && rel_5_symlog_domain_symlog_symbolic_2->contains(Tuple<RamDomain,1>{{ramBitCast(env0[3])}},READ_OP_CONTEXT(rel_5_symlog_domain_symlog_symbolic_2_op_ctxt)) && rel_3_symlog_domain_symlog_symbolic_0->contains(Tuple<RamDomain,1>{{ramBitCast(env0[1])}},READ_OP_CONTEXT(rel_3_symlog_domain_symlog_symbolic_0_op_ctxt))) {
auto range = rel_2_LoadArrayIndex->lowerUpperRange_00010(Tuple<RamDomain,5>{{ramBitCast<RamDomain>(MIN_RAM_SIGNED), ramBitCast<RamDomain>(MIN_RAM_SIGNED), ramBitCast<RamDomain>(MIN_RAM_SIGNED), ramBitCast(env0[0]), ramBitCast<RamDomain>(MIN_RAM_SIGNED)}},Tuple<RamDomain,5>{{ramBitCast<RamDomain>(MAX_RAM_SIGNED), ramBitCast<RamDomain>(MAX_RAM_SIGNED), ramBitCast<RamDomain>(MAX_RAM_SIGNED), ramBitCast(env0[0]), ramBitCast<RamDomain>(MAX_RAM_SIGNED)}},READ_OP_CONTEXT(rel_2_LoadArrayIndex_op_ctxt));
for(const auto& env1 : range) {
Tuple<RamDomain,7> tuple{{ramBitCast(env1[4]),ramBitCast(env1[1]),ramBitCast(RamSigned(33)),ramBitCast(env0[1]),ramBitCast(env0[2]),ramBitCast(env0[3]),ramBitCast(env0[4])}};
rel_9_NullAt->insert(tuple,READ_OP_CONTEXT(rel_9_NullAt_op_ctxt));
}
}
}
}
();}
if (pruneImdtRels) rel_2_LoadArrayIndex->purge();
if (pruneImdtRels) rel_8_VarPointsToNull->purge();
}
#ifdef _MSC_VER
#pragma warning(default: 4100)
#endif // _MSC_VER
#ifdef _MSC_VER
#pragma warning(disable: 4100)
#endif // _MSC_VER
void subroutine_11(const std::vector<RamDomain>& args, std::vector<RamDomain>& ret) {
signalHandler->setMsg(R"_(Reachable("<ArrayNullLoad: void main(java.lang.String[])>").
in file small_transformed_program.dl [35:1-35:61])_");
[&](){
CREATE_OP_CONTEXT(rel_10_Reachable_op_ctxt,rel_10_Reachable->createContext());
Tuple<RamDomain,1> tuple{{ramBitCast(RamSigned(6))}};
rel_10_Reachable->insert(tuple,READ_OP_CONTEXT(rel_10_Reachable_op_ctxt));
}
();}
#ifdef _MSC_VER
#pragma warning(default: 4100)
#endif // _MSC_VER
};
SouffleProgram *newInstance_small_transformed(){return new Sf_small_transformed;}
SymbolTable *getST_small_transformed(SouffleProgram *p){return &reinterpret_cast<Sf_small_transformed*>(p)->getSymbolTable();}

#ifdef __EMBEDDED_SOUFFLE__
class factory_Sf_small_transformed: public souffle::ProgramFactory {
SouffleProgram *newInstance() {
return new Sf_small_transformed();
};
public:
factory_Sf_small_transformed() : ProgramFactory("small_transformed"){}
};
extern "C" {
factory_Sf_small_transformed __factory_Sf_small_transformed_instance;
}
}
#else
}
int main(int argc, char** argv)
{
try{
souffle::CmdOptions opt(R"(small_transformed_program.dl)",
R"()",
R"()",
false,
R"()",
1);
if (!opt.parse(argc,argv)) return 1;
souffle::Sf_small_transformed obj;
#if defined(_OPENMP) 
obj.setNumThreads(opt.getNumJobs());

#endif
obj.runAll(opt.getInputFileDir(), opt.getOutputFileDir());
return 0;
} catch(std::exception &e) { souffle::SignalHandler::instance()->error(e.what());}
}

#endif

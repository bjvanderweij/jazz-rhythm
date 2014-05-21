"""JazzR

A Library of midi tools and algorithms for analysing rhythm in jazz music
"""

# Borrowed from jazzparser.data

class Fraction(object):
    """
    Stores a rational fraction as a numerator and denominator.
    Fractions can be output as strings and also read in from strings
    (use Fraction(string=<string>), or just Fraction(<string>)).

    The format used is "i", where i
    is an integer if the fraction is an exact integer, or "i n/d", where
    i is the integer part, n the numerator and d the denominator.

    """
    def __init__(self, numerator=0, denominator=1, string=None):
        self._denominator = 1

        self.numerator = numerator
        self.denominator = denominator
        if isinstance(numerator, str):
            string = numerator
        if string is not None:
            whole_string = string
            # Get rid of extra spaces
            string = string.strip()
            # Check for negation at the beginning: has to negate whole fraction
            # If we don't split this off now, it only negates the integer part
            if string.startswith("-"):
                neg = True
                string = string.lstrip("-").strip()
            else:
                neg = False
            # Split the integer part from the fractional part
            string_parts = string.split(" ")
            try:
                if len(string_parts) == 1:
                    # Try splitting into a/b
                    fract_parts = [p.strip() for p in string.split("/")]
                    if len(fract_parts) == 1:
                        # Just an integer
                        self.numerator = int(string)
                        self.denominator = 1
                    elif len(fract_parts) == 2:
                        # a/b
                        self.numerator = int(fract_parts[0])
                        self.denominator = int(fract_parts[1])
                    else:
                        raise Fraction.ValueError, "Too many slashes in "\
                            "fraction '%s'." % whole_string
                else:
                    integer = int(string_parts[0])
                    fract_parts = string_parts[1].split("/")
                    if len(fract_parts) == 2:
                        numerator = int(fract_parts[0])
                        denominator = int(fract_parts[1])
                    else:
                        raise Fraction.ValueError, "Too many slashes in "\
                            "fraction '%s'." % whole_string
                    self.numerator = numerator + integer * denominator
                    self.denominator = denominator
            except ValueError:
                raise Fraction.ValueError, "Error parsing fraction "\
                    "string '%s'." % string
            if neg:
                # There was a - at the beginning, so negate the whole thing
                self.numerator = -self.numerator

    def _get_denominator(self):
        return self._denominator
    def _set_denominator(self, val):
        if val == 0:
            raise ZeroDivisionError, "tried to set a Fraction's denominator "\
                "to zero"
        self._denominator = val
    denominator = property(_get_denominator, _set_denominator)

    def simplify(self):
        # Find the highest common factor of the num and denom
        hcf = euclid(self.numerator, self.denominator)
        if hcf != 0:
            self.numerator /= hcf
            self.denominator /= hcf

    def simplified(self):
        """
        Returns a simplified version of this fraction without modifying
        the instance.

        """
        # Find the highest common factor of the num and denom
        hcf = euclid(self.numerator, self.denominator)
        if hcf == 0:
            numerator = self.numerator
            denominator = self.denominator
        else:
            numerator = self.numerator / hcf
            denominator = self.denominator / hcf
        return Fraction(numerator, denominator)

    def reciprocal(self):
        if self.numerator == 0:
            raise ZeroDivisionError, "tried to take reciprocal of 0"
        return Fraction(self.denominator, self.numerator)

    def __str__(self):
        if self.denominator == 1:
            return "%d" % self.numerator
        elif self.numerator/self.denominator == 0:
            return "%d/%d" % (self.numerator, self.denominator)
        else:
            return "%d %d/%d" % (self.numerator/self.denominator, \
                                 self.numerator % self.denominator, \
                                 self.denominator)

    __repr__ = __str__

    def to_latex(self):
        if self.denominator == 1:
            return "%d" % self.numerator
        else:
            return "%d \\frac{%d}{%d}" % (self.numerator/self.denominator, \
                                 self.numerator % self.denominator, \
                                 self.denominator)

    ####### Operator overloading #######

    def __add__(self, other):
        if type(other) == int or type(other) == long:
            result = Fraction(self.numerator + other*self.denominator, self.denominator)
        elif type(other) == Fraction:
            new_denom = self.denominator * other.denominator
            result = Fraction((self.numerator*other.denominator \
                               + other.numerator*self.denominator), new_denom)
        elif type(other) == float:
            return float(self) + other
        else:
            raise TypeError, "unsupported operand type for - with Fraction: %s" % type(other)
        result.simplify()
        return result

    # For backwards compatibility...
    plus = __add__

    def __radd__(self, other):
        # Addition works the same both ways
        return self + other

    def __neg__(self):
        return Fraction(-self.numerator, self.denominator)

    def __sub__(self, other):
        return self + (-other)

    def __rsub__(self, other):
        return (-self) + other

    def __mul__(self, other):
        if type(other) == int or type(other) == long:
            result = Fraction(self.numerator*other, self.denominator)
        elif type(other) == Fraction:
            result = Fraction(self.numerator*other.numerator, self.denominator*other.denominator)
        elif type(other) == float:
            return float(self) * other
        else:
            raise TypeError, "unsupported operand type for * with Fraction: %s" % type(other)
        result.simplify()
        return result

    def __rmul__(self, other):
        # Multiplication works the same both ways
        return self * other

    def __div__(self, other):
        if type(other) == int or type(other) == long:
            result = Fraction(self.numerator, self.denominator*other)
        elif type(other) == Fraction:
            result = Fraction(self.numerator*other.denominator, self.denominator*other.numerator)
        elif type(other) == float:
            return float(self) / other
        else:
            raise TypeError, "unsupported operand type for / with Fraction: %s" % type(other)
        result.simplify()
        return result

    def __rdiv__(self, other):
        return self.reciprocal() * other

    def __float__(self):
        return float(self.numerator) / self.denominator

    def __int__(self):
        return self.numerator / self.denominator

    def __long__(self):
        return long(self.numerator) / long(self.denominator)

    #####################################

    def __cmp__(self, other):
        if other is None:
            return 1

        if type(other) == int:
            other = Fraction(other)

        if type(other) == float:
            return cmp(float(self), other)

        if other.__class__ != self.__class__:
            raise TypeError, "Fraction.__cmp__(self,other) requires other to "\
                "be of type Fraction or int. Type was %s." % other.__class__
        # Cmp should not have any lasting effect on the objects
        selfnum = self.numerator
        othernum = other.numerator
        selfnum *= other.denominator
        othernum *= self.denominator
        if selfnum == othernum:
            return 0
        elif selfnum > othernum:
            return 1
        else:
            return -1

    def __hash__(self):
        return self.numerator + self.denominator

    class ValueError(Exception):
        pass

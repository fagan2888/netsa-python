# Copyright 2008-2010 by Carnegie Mellon University

# @OPENSOURCE_HEADER_START@
# Use of the Network Situational Awareness Python support library and
# related source code is subject to the terms of the following licenses:
# 
# GNU Public License (GPL) Rights pursuant to Version 2, June 1991
# Government Purpose License Rights (GPLR) pursuant to DFARS 252.225-7013
# 
# NO WARRANTY
# 
# ANY INFORMATION, MATERIALS, SERVICES, INTELLECTUAL PROPERTY OR OTHER 
# PROPERTY OR RIGHTS GRANTED OR PROVIDED BY CARNEGIE MELLON UNIVERSITY 
# PURSUANT TO THIS LICENSE (HEREINAFTER THE "DELIVERABLES") ARE ON AN 
# "AS-IS" BASIS. CARNEGIE MELLON UNIVERSITY MAKES NO WARRANTIES OF ANY 
# KIND, EITHER EXPRESS OR IMPLIED AS TO ANY MATTER INCLUDING, BUT NOT 
# LIMITED TO, WARRANTY OF FITNESS FOR A PARTICULAR PURPOSE, 
# MERCHANTABILITY, INFORMATIONAL CONTENT, NONINFRINGEMENT, OR ERROR-FREE 
# OPERATION. CARNEGIE MELLON UNIVERSITY SHALL NOT BE LIABLE FOR INDIRECT, 
# SPECIAL OR CONSEQUENTIAL DAMAGES, SUCH AS LOSS OF PROFITS OR INABILITY 
# TO USE SAID INTELLECTUAL PROPERTY, UNDER THIS LICENSE, REGARDLESS OF 
# WHETHER SUCH PARTY WAS AWARE OF THE POSSIBILITY OF SUCH DAMAGES. 
# LICENSEE AGREES THAT IT WILL NOT MAKE ANY WARRANTY ON BEHALF OF 
# CARNEGIE MELLON UNIVERSITY, EXPRESS OR IMPLIED, TO ANY PERSON 
# CONCERNING THE APPLICATION OF OR THE RESULTS TO BE OBTAINED WITH THE 
# DELIVERABLES UNDER THIS LICENSE.
# 
# Licensee hereby agrees to defend, indemnify, and hold harmless Carnegie 
# Mellon University, its trustees, officers, employees, and agents from 
# all claims or demands made against them (and any related losses, 
# expenses, or attorney's fees) arising out of, or relating to Licensee's 
# and/or its sub licensees' negligent use or willful misuse of or 
# negligent conduct or willful misconduct regarding the Software, 
# facilities, or other rights or assistance granted by Carnegie Mellon 
# University under this License, including, but not limited to, any 
# claims of product liability, personal injury, death, damage to 
# property, or violation of any laws or regulations.
# 
# Carnegie Mellon University Software Engineering Institute authored 
# documents are sponsored by the U.S. Department of Defense under 
# Contract F19628-00-C-0003. Carnegie Mellon University retains 
# copyrights in all material produced under this contract. The U.S. 
# Government retains a non-exclusive, royalty-free license to publish or 
# reproduce these documents, or allow others to do so, for U.S. 
# Government purposes only pursuant to the copyright license under the 
# contract clause at 252.227.7013.
# @OPENSOURCE_HEADER_END@

class AuditException(Exception):
    pass

class AuditError(AuditException):
    pass

class AuditSourceError(AuditError):
    pass

class AuditStampError(AuditError):
    pass

class AuditSourceNotFound(AuditException):
    pass

class AuditNotFound(AuditException):
    pass

class AuditStampNotFound(AuditException):
    pass

class AuditMismatch(AuditException):
    pass

class AuditRefresh(AuditException):
    pass

###

class SentinelAuditor(object):
    """
    Base class for sentinel auditors. Subclasses must at minumum
    provide the audit() and stamp() methods. A key() method is a good
    idea as well.
    """

    def key(self):
        """
        Key to use in a dictionary of resource states. We deliberately
        don't use the __hash__() method since we are not trying to embed
        auditor objects in the dictionary.
        """
        return str(self)

    def audit(self, stamp):
        """
        Compares the current state of the resource with the provided
        cached state. Must be overridden in a subclass.
        """
        raise RuntimeError, "override in subclass"

    def stamp(self):
        """
        Calculates the current state of the resource. Must be overridden
        in a subclass.
        """
        raise RuntimeError, "override in subclass"

    def validate(self, stamp):
        """
        Determines whether the the given stamp is well-formed or not.
        This has no bearing on whether the values within the stamp
        reflect the current state of the data source. Returns False on
        failure, or the stamp itself on success.
        """
        return stamp

    def __cachekey__(self):
        return str(self)

    def __cmp__(self, other):
        return self.__cachekey__() == other.__cachekey__()

    def __hash__(self):
        return self.__cachekey__().__hash__()

###

__all__ = [

    'SentinelAuditor',

    'AuditException',
    'AuditError',
    'AuditSourceError',
    'AuditStampError',
    'AuditSourceNotFound',
    'AuditNotFound',
    'AuditStampNotFound',
    'AuditMismatch',
    'AuditRefresh',

]
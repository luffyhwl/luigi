# -*- coding: utf-8 -*-
#
# Copyright 2012-2015 Spotify AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import functools
import itertools
import sys

from luigi import six

# import unittest on python 2.6 for support of test skip
if sys.version_info[:2] <= (2, 6):
    try:
        import unittest2 as unittest
    except ImportError:
        import unittest
else:
    import unittest


class with_config(object):
    """
    Decorator to override config settings for the length of a function.

    Usage:

    .. code-block: python

        >>> import luigi.configuration
        >>> @with_config({'foo': {'bar': 'baz'}})
        ... def my_test():
        ...     print(luigi.configuration.get_config().get("foo", "bar"))
        ...
        >>> my_test()
        baz
        >>> @with_config({'hoo': {'bar': 'buz'}})
        ... @with_config({'foo': {'bar': 'baz'}})
        ... def my_test():
        ...     print(luigi.configuration.get_config().get("foo", "bar"))
        ...     print(luigi.configuration.get_config().get("hoo", "bar"))
        ...
        >>> my_test()
        baz
        buz
        >>> @with_config({'foo': {'bar': 'buz'}})
        ... @with_config({'foo': {'bar': 'baz'}})
        ... def my_test():
        ...     print(luigi.configuration.get_config().get("foo", "bar"))
        ...
        >>> my_test()
        baz
        >>> @with_config({'foo': {'bur': 'buz'}})
        ... @with_config({'foo': {'bar': 'baz'}})
        ... def my_test():
        ...     print(luigi.configuration.get_config().get("foo", "bar"))
        ...     print(luigi.configuration.get_config().get("foo", "bur"))
        ...
        >>> my_test()
        baz
        buz
        >>> @with_config({'foo': {'bur': 'buz'}})
        ... @with_config({'foo': {'bar': 'baz'}}, replace_sections=True)
        ... def my_test():
        ...     print(luigi.configuration.get_config().get("foo", "bar"))
        ...     print(luigi.configuration.get_config().get("foo", "bur", "no_bur"))
        ...
        >>> my_test()
        baz
        no_bur

    """

    def __init__(self, config, replace_sections=False):
        self.config = config
        self.replace_sections = replace_sections

    def _make_dict(self, old_dict):
        if self.replace_sections:
            old_dict.update(self.config)
            return old_dict

        def get_section(sec):
            old_sec = old_dict.get(sec, {})
            new_sec = self.config.get(sec, {})
            old_sec.update(new_sec)
            return old_sec

        all_sections = itertools.chain(old_dict.keys(), self.config.keys())
        return {sec: get_section(sec) for sec in all_sections}

    def __call__(self, fun):
        @functools.wraps(fun)
        def wrapper(*args, **kwargs):
            import luigi.configuration
            orig_conf = luigi.configuration.LuigiConfigParser.instance()
            new_conf = luigi.configuration.LuigiConfigParser()
            luigi.configuration.LuigiConfigParser._instance = new_conf
            orig_dict = {k: dict(orig_conf.items(k)) for k in orig_conf.sections()}
            new_dict = self._make_dict(orig_dict)
            for (section, settings) in six.iteritems(new_dict):
                new_conf.add_section(section)
                for (name, value) in six.iteritems(settings):
                    new_conf.set(section, name, value)
            try:
                return fun(*args, **kwargs)
            finally:
                luigi.configuration.LuigiConfigParser._instance = orig_conf
        return wrapper

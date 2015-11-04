# vim: set encoding=utf-8
import string
from pyparsing import Word, Literal

""" Contruct a grammar that parses references/citations to the United States
Code, the Code of Federal Regulations, Public Law and Statues at Large. """

uscode_exp = Word(string.digits) + "U.S.C." + Word(string.digits)

cfr_exp_v1 = Word(string.digits) + "CFR" + "part" + Word(string.digits)

cfr_exp_v2 = Word(string.digits) + "CFR" +\
    Word(string.digits) + "." + Word(string.digits)

cfr_exp = cfr_exp_v1.setResultsName('V1') ^ cfr_exp_v2.setResultsName('V2')

the_act_exp = Literal("the") + Literal("Act")

public_law_exp = Literal("Public") + Literal("Law") +\
    Word(string.digits) + '-' + Word(string.digits)

stat_at_large_exp = Word(string.digits) +\
    Literal("Stat.") + Word(string.digits)

regtext_external_citation = uscode_exp.setResultsName('USC') |\
    cfr_exp | the_act_exp | public_law_exp | stat_at_large_exp

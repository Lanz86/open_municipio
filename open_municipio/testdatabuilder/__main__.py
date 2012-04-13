from optparse import OptionParser
from open_municipio.testdatabuilder import RandomItemsFactory

if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option("-p", "--part", dest="part",
                      help="part to run (people|acts|votations)", metavar="PART")

    (options, args) = parser.parse_args()

    if options.part == 'people':
        RandomItemsFactory().generate_people_dataset()
    elif options.part == 'votations':
        RandomItemsFactory().generate_votations_dataset()
    else:
        RandomItemsFactory().generate_acts_dataset()

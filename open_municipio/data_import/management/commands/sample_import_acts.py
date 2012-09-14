# -*- coding: utf-8 -*-
from optparse import make_option
import os
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.management.base import LabelCommand, CommandError, BaseCommand
from django.core.files import File

from lxml import etree, html
from os import path

from open_municipio.data_import.utils import netcat
from haystack.backends.solr_backend import SolrSearchBackend
from open_municipio.people.models import Person, municipality
from open_municipio.acts.models import *

import logging

from open_municipio.data_import import conf


# configure xml namespaces
NS = {
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'om': 'http://www.openmunicipio.it',
    'xlink': 'http://www.w3.org/1999/xlink'
}
XLINK_NAMESPACE = NS['xlink']
XLINK = "{%s}" % XLINK_NAMESPACE


class Command(LabelCommand):
    option_list = BaseCommand.option_list + (
        make_option('--overwrite',
                    action='store_true',
                    dest='overwrite',
                    default=False,
                    help='Re-write act from scratch'
        ),
        make_option('--people-file',
                    dest='people_file',
                    default=conf.ACTS_PEOPLE_FILE,
                    help='The xml file containing the persons ids mappings'
        ),
        make_option('--act-type',
                    dest='act_type',
                    default='CouncilDeliberation',
                    help='The type of act to import'
        ),
    )

    args = "<filename filename ...>"
    help = "Import the act(s) of type act_type, contained in the specified XML document(s)."
    label = 'filename'

    logger = logging.getLogger('import')

    people_tree = None

    def lookupCharge(self, xml_chargexref, institution=None):
        """
        look for the correct open municipio charge, or return None
        """
        try:
            file, charge_id = xml_chargexref.get(XLINK+"href").split("#")
            people_charges = self.people_tree.xpath(
                '//om:Person[@id="%s"]' % charge_id,
                namespaces=NS
            )
            if len(people_charges):
                om_id = people_charges[0].get('om_id')
                if om_id is None:
                    self.logger.warning("charge with id %s has no om_id (past charge?). Skipping." % charge_id)
                    return None
                charge_type = people_charges[0].get('charge')
                if charge_type is None:
                    self.logger.warning("charge with id %s has no charge attribute. Skipping." % charge_id)
                    return None

                # institution is grabbed from charge attribute, in acts import
                # since mayor and deputies may sign acts, not only counselor
                if charge_type == 'counselor':
                    institution = municipality.council.as_institution
                elif charge_type == 'deputy' or charge_type == 'firstdeputy':
                    institution = municipality.gov.as_institution
                elif charge_type == 'mayor':
                    institution = municipality.mayor.as_institution
                else:
                    self.stderr.write("Warning: charge with id %s has wrong charge attribute %s. Skipping.\n" %
                                      (charge_id, charge_type))
                    return None

                try:
                    person = Person.objects.get(pk=int(om_id))
                    charge =  person.current_institution_charge(institution)
                    return charge
                except ObjectDoesNotExist:
                    self.logger.warning("could not find person or charge for id = %s in open municipio DB. Skipping." % charge_id)
                    return None
                except MultipleObjectsReturned:
                    self.stderr.write("Error: found more than one person or charge for id %s in open municipio db. Skipping.\n" % charge_id)
                    return None
            else:
                self.logger.warning("could not find person for id %s in peopkle XML file. Skipping." % charge_id)
                return None
        except ObjectDoesNotExist:
            self.logger.warning("could not find charge with id %s in Open Municipio DB. Skipping." % component_id)
            return None

    def fetch_signers(self, om_act, xml_subscribers_set, support_type, charge_lookup_institution):
        """
        extract signers from an om:ActSubscribers tag and build related ActSupport records
        om_act - the Act instance supported
        xml_subscribers_set - the om:ActSubscribers xml node
        support_type - the type of support (first_signer, co_signer)
        """

        # build an ActSupport for every single charge
        supports = xml_subscribers_set.xpath("./om:ActSupport", namespaces=NS)
        self.logger.info(" ActSubscriber contains %d ActSupports" % len(supports))
        for xml_support in supports:
            support_date = xml_support.get("date")
            # if date is not specified, get it from act's presentation date
            if support_date is None:
                support_date = om_act.presentation_date

            chargexref = xml_support.xpath("./om:ChargeXRef", namespaces=NS)[0]
            om_charge = self.lookupCharge(chargexref, charge_lookup_institution)
            if om_charge is None:
                continue

            # add act support for this charge
            om_as, created = ActSupport.objects.get_or_create(
                charge=om_charge,
                act=om_act,
                support_type=support_type
            )

            # always rewrite support date
            om_as.support_date = support_date
            om_as.save()

    def fetch_attachments(self, filename, om_act, xml_act):
        """
        fetch all attachments for the act in the XML
        om_act - related Act instance
        xml_act - act xml node
        """

        attachments = xml_act.xpath("./om:Attachment", namespaces=NS)
        self.logger.info("%d Attachments to import" % len(attachments))
        for xml_attach in attachments:

            attach_title = xml_attach.get("title")
            if attach_title is None:
                self.stderr.write(
                    "Error: Attach has no title! Skipping this sitting." % id
                )
                continue

            attach_href = xml_attach.get(XLINK+"href")
            if attach_href is None:
                self.stderr.write(
                    "Attachment has no xlink:href attribute! Skipping it."
                )
                continue

            attach_dir = attach_href.split('/')[-2]
            attach_file = path.join(path.dirname(filename), attach_href)
            if not path.isfile(attach_file):
                self.stderr.write("File %s does not exist. Skipping!\n" % attach_file)
                continue

            # build a new attach only if old is not found
            om_att, created = Attach.objects.get_or_create(
                act=om_act,
                title=attach_title
            )
            om_att.document_date = om_act.presentation_date
            om_att.save()

            # remove old attach file to avoid _1 files whenb rewriting
            try:
                old_attach_file = om_att.file.file
                os.remove(old_attach_file.name)
            except ValueError:
                pass

            # overwrite attach file and save it under media (/uploads)
            attach_filename = path.basename(attach_file)
            attach_f = open(attach_file, 'r')
            om_att.file.save(attach_dir + "_" + attach_filename, File(attach_f))
            om_att.document_type = os.path.splitext(attach_filename)[1][1:]
            om_att.document_size = File(attach_f).size
            self.logger.info(" will attach %s - %s (%s)" % (attach_file, attach_title, attach_dir + "_" + attach_filename))
            om_att.save()

            # text extraction (using tika inside solr)
            if 'testoproposta' in attach_filename.lower() or\
               'testodiscussione' in attach_filename.lower():

                """
                Streamlines content extraction from a doc (pdf, or other format file, as specified in Tika) within a solr request.
                Requires Haystack 2.0.0.
                Handles unicode characters, as well.

                In settings, define this hash:
                HAYSTACK_CONNECTIONS = {
                    'default': {
                        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
                        'URL': 'http://127.0.0.1:8983/solr',
                        'TIMEOUT': 60 * 5,
                        'BATCH_SIZE': 100,
                        'SEARCH_RESULTS_PER_PAGE': 10,
                    }
                }


                from django.conf import settings
                from haystack.backends.solr_backend import SolrSearchBackend
                from lxml import html

                file_path = '/Users/guglielmo/Workspace/open_municipio/test_data/acts/20120622_ATTI_2008/DC_2008401100013/TestoProposta.doc'
                solr_backend = SolrSearchBackend('default', **settings.HAYSTACK_CONNECTIONS['default'])

                attach_f = open(file_path)
                file_content = solr_backend.extract_file_contents(attach_f)
                html_content = html.fromstring(file_content['contents'].encode('utf-8'))
                document_text = html_content.cssselect('body')[0].text_content()

                print document_text
                """


                # reset attach file pointer
                attach_f.seek(0)

                # text extraction, through haystack-solr and lxml.html
                solr_backend = SolrSearchBackend('default', **settings.HAYSTACK_CONNECTIONS['default'])
                file_content = solr_backend.extract_file_contents(attach_f)
                html_content = html.fromstring(file_content['contents'].encode('utf-8'))
                document_text = html_content.cssselect('body')[0].text_content()

                # text content saved into attachment's text
                om_att.text = document_text
                om_att.save()

                # for proposale, text content goes into act's content field
                if 'testoproposta' in attach_filename.lower():
                    om_act.text = document_text
                    om_act.save()

    def handle_deliberation(self, filename, **options):

        tree = etree.parse(filename)

        acts = tree.xpath("/om:CouncilDeliberation",namespaces=NS)
        self.logger.info("%d Deliberation to import" % len(acts))
        for xml_act in acts:

            # get important attributes
            id = xml_act.get("id")
            if id is None:
                self.stderr.write(
                    "Error: Act has no id attribute! Skipping this sitting."
                )
                continue

            final_id = xml_act.get('final_id')

            initiative = conf.XML_TO_OM_INITIATIVE[xml_act.get("initiative")]
            if initiative is None:
                self.stderr.write(
                    "Error: Act %s has no initiative attribute! Skipping this sitting." % id
                )
                continue
                # transform xml value into database string
            initiative = Deliberation.INITIATIVE_TYPES.__dict__['_choice_dict'][initiative]

            presentation_date = xml_act.get("presentation_date")
            if presentation_date is None:
                self.stderr.write(
                    "Error: Act %s has no presentation_date attribute! Skipping this sitting." % id
                )
                continue

            title = xml_act.xpath("./om:Title", namespaces=NS)
            if title is None:
                self.stderr.write(
                    "Error: Act %s has no title attribute! Skipping this sitting." % id
                )
                continue
            title = title[0].text


            # get or create the deliberation object
            curr_inst = municipality.council.as_institution
            om_act, created = Deliberation.objects.get_or_create(
                idnum=id,
                presentation_date=presentation_date,
                emitting_institution=curr_inst,
                initiative=initiative,
                title=title
            )

            if not created:
                self.logger.info("Found deliberation %s" % om_act.idnum)
            else:
                self.logger.info("Created deliberation %s" % om_act.idnum)

            # fetch all subscribers for the act in the XML
            subscribers = xml_act.xpath("./om:ActSubscribers", namespaces=NS)
            self.logger.info("%d Subscribers sets to import" % len(subscribers))
            for xml_subscribers_set in subscribers:

                # check that support type exists (for deliberations)
                support_type = xml_subscribers_set.get("type")
                if support_type is None:
                    self.stderr.write(
                        "ActSubscriber has no type attribute! Skipping it."
                    )
                    continue

                # map xml support types to ours (first_signer and co_signer)
                if support_type == 'first_subscriber':
                    support_type = ActSupport.SUPPORT_TYPE.first_signer
                else:
                    support_type = ActSupport.SUPPORT_TYPE.co_signer

                self.fetch_signers(om_act, xml_subscribers_set, support_type, curr_inst)


            self.fetch_attachments(filename, om_act, xml_act)

            # call parent class save to trigger
            # real-time search index update
            # since signals do not handle hierarchy well
            om_act.act_ptr.save()

    def handle_interrogation(self, filename, **options):

        tree = etree.parse(filename)

        acts = tree.xpath("/om:Interrogation",namespaces=NS)
        self.logger.info("%d Interrogations to import" % len(acts))
        for xml_act in acts:

            # get important attributes
            id = xml_act.get("id")
            if id is None:
                self.stderr.write(
                    "Error: Act has no id attribute! Skipping this sitting."
                )
                continue

            presentation_date = xml_act.get("presentation_date")
            if presentation_date is None:
                self.stderr.write(
                    "Error: Act %s has no presentation_date attribute! Skipping this sitting." % id
                )
                continue

            answer_type = xml_act.get("answer_type")
            if answer_type is None:
                self.stderr.write(
                    "Error: Act %s has no answer_type attribute! Skipping this sitting." % id
                )
                continue

            title = xml_act.xpath("./om:Title", namespaces=NS)
            if title is None:
                self.stderr.write(
                    "Error: Act %s has no title attribute! Skipping this sitting." % id
                )
                continue
            title = title[0].text


            # get or create the interrogation object
            curr_inst = municipality.council.as_institution
            om_act, created = Interrogation.objects.get_or_create(
                idnum=id,
                presentation_date=presentation_date,
                emitting_institution=curr_inst,
                answer_type=answer_type,
                title=title
            )

            if not created:
                self.logger.info("Found interrogation %s" % om_act.idnum)
            else:
                self.logger.info("Created interrogation %s" % om_act.idnum)

            # fetch all subscribers for the act in the XML
            subscribers = xml_act.xpath("./om:ActSubscribers", namespaces=NS)
            self.logger.info("%d Subscribers sets to import" % len(subscribers))
            for xml_subscribers_set in subscribers:

                # support type for interrogations are always first_signer
                support_type = ActSupport.SUPPORT_TYPE.first_signer

                #fetch signers for the subscribers set
                self.fetch_signers(om_act, xml_subscribers_set, support_type, curr_inst)

            self.fetch_attachments(filename, om_act, xml_act)

            # call parent class save to trigger
            # real-time search index update
            # since signals do not handle hierarchy well
            om_act.act_ptr.save()

    def handle_motion(self, filename, **options):

        tree = etree.parse(filename)

        acts = tree.xpath("/om:Motion",namespaces=NS)
        self.logger.info("%d Motions to import" % len(acts))
        for xml_act in acts:

            # get important attributes
            id = xml_act.get("id")
            if id is None:
                self.stderr.write(
                    "Error: Act has no id attribute! Skipping this sitting."
                )
                continue

            presentation_date = xml_act.get("presentation_date")
            if presentation_date is None:
                self.stderr.write(
                    "Error: Act %s has no presentation_date attribute! Skipping this sitting." % id
                )
                continue

            title = xml_act.xpath("./om:Title", namespaces=NS)
            if title is None:
                self.stderr.write(
                    "Error: Act %s has no title attribute! Skipping this sitting." % id
                )
                continue
            title = title[0].text


            # get or create the interrogation object
            curr_inst = municipality.council.as_institution
            om_act, created = Motion.objects.get_or_create(
                idnum=id,
                presentation_date=presentation_date,
                emitting_institution=curr_inst,
                title=title
            )

            if not created:
                self.logger.info("Found motion %s" % om_act.idnum)
            else:
                self.logger.info("Created motion %s" % om_act.idnum)

            # fetch all subscribers for the act in the XML
            subscribers = xml_act.xpath("./om:ActSubscribers", namespaces=NS)
            self.logger.info("%d Subscribers sets to import" % len(subscribers))
            for xml_subscribers_set in subscribers:

                # support type for interrogations are always first_signer
                support_type = ActSupport.SUPPORT_TYPE.first_signer

                #fetch signers for the subscribers set
                self.fetch_signers(om_act, xml_subscribers_set, support_type, curr_inst)

            self.fetch_attachments(filename, om_act, xml_act)

            # call parent class save to trigger
            # real-time search index update
            # since signals do not handle hierarchy well
            om_act.act_ptr.save()

    def handle_label(self, filename, **options):
        if not path.isfile(filename):
            raise IOError("File %s does not exist" % filename)

        act_type = options['act_type']
        if act_type == 'CouncilDeliberation':
            self.handle_deliberation(filename, **options)
        elif act_type == 'Interrogation':
            self.handle_interrogation(filename, **options)
        elif act_type == 'Motion':
            self.handle_motion(filename, **options)
        else:
            raise IOError("Act type %s not known" % options['act_type'])

    def handle(self, *labels, **options):
        if not labels:
            raise CommandError('Enter at least one %s.' % self.label)

        # parse people xml file into an lxml.etree
        people_file = options['people_file']
        if not path.isfile(people_file):
            raise IOError("File %s does not exist" % people_file)

        self.people_tree = etree.parse(people_file)

        # parse passed acts
        for label in labels:
            self.handle_label(label, **options)
        return 'done\n'

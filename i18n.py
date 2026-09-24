"""Greek version of the site. English stays at /, Greek is served under /el/.

UI and content strings are keyed by their English text, so templates stay readable
and a missing translation falls back to English. Greek product copy lives in
data/products_el.json keyed by slug, because tools/build_catalog.py rewrites
products.json from scratch.
"""
import json
import re
import unicodedata

from content import BRANDS, HERO, PRODUCTS, PRODUCTS_BY_SLUG, ROOT

LANGS = ("en", "el")
DEFAULT_LANG = "en"
LANG_LABELS = {"en": "EN", "el": "ΕΛ"}
OG_LOCALES = {"en": "en_CY", "el": "el_GR"}

EL = {
    # Header, footer, shared labels
    "Skip to content": "Μετάβαση στο περιεχόμενο",
    "Language": "Γλώσσα",
    "Primary": "Κύριο μενού",
    "Menu": "Μενού",
    "Catalogue": "Κατάλογος",
    "Order": "Παραγγελία",
    "B2B Services": "Υπηρεσίες B2B",
    "Contact": "Επικοινωνία",
    "Official Cyprus representative of Vittorio Gourmet Espresso and Jean Paul Lab":
        "Επίσημος αντιπρόσωπος στην Κύπρο της Vittorio Gourmet Espresso και της Jean Paul Lab",
    "Free delivery over €40": "Δωρεάν παράδοση άνω των €40",
    "Footer": "Υποσέλιδο",
    "Official representative in Cyprus": "Επίσημος αντιπρόσωπος στην Κύπρο",
    "Coffee, beverages and café supplies, delivered across Cyprus.":
        "Καφές, ροφήματα και αναλώσιμα, με παράδοση σε όλη την Κύπρο.",
    "Explore": "Πλοήγηση",
    "Based in": "Έδρα",
    "Social": "Κοινωνικά δίκτυα",
    "Legal": "Νομικά",
    "Privacy": "Απόρρητο",
    "Returns": "Επιστροφές",
    "Questions": "Ερωτήσεις",
    "Prices exclude VAT. Payment is cash on delivery.":
        "Οι τιμές δεν περιλαμβάνουν ΦΠΑ. Πληρωμή με μετρητά κατά την παράδοση.",
    "Kalo Xorio": "Καλό Χωριό",
    "Larnaca": "Λάρνακα",
    "Cyprus": "Κύπρος",
    "Contact on Viber": "Επικοινωνία στο Viber",
    "Website": "Ιστότοπος",
    # Product cards and product page
    "Add to order": "Προσθήκη",
    "Qty": "Ποσότητα",
    "Pack size": "Συσκευασία",
    "Free delivery over €40 · Cash on delivery": "Δωρεάν παράδοση άνω των €40 · Αντικαταβολή",
    "Dietary note": "Διατροφική σημείωση",
    "All {brand} products": "Όλα τα προϊόντα {brand}",
    "More from {brand}": "Περισσότερα προϊόντα {brand}",
    "Back to {group}": "Πίσω στην κατηγορία «{group}»",
    "Price not published": "Τιμή κατόπιν ζήτησης",
    "Price on request": "Τιμή κατόπιν ζήτησης",
    # Catalogue groups and brand filters
    "Coffee": "Καφές",
    "Aromatic chocolates": "Αρωματικές σοκολάτες",
    "Chocolate powders": "Σοκολάτες σε σκόνη",
    "Soft ice cream": "Παγωτό soft",
    "Coffee syrups": "Σιρόπια καφέ",
    "Smoothies": "Smoothies",
    "Milkshakes": "Milkshakes",
    "Teas": "Τσάγια",
    "Café mixes": "Μείγματα γλυκών",
    "Granitas": "Γρανίτες",
    "Serviceware": "Αναλώσιμα",
    "Café essentials": "Αναλώσιμα καφέ",
    # Brands
    "Italian-style espresso since 2000": "Espresso ιταλικού τύπου από το 2000",
    "Espresso blends, single origins, Greek and filter coffee, and chocolate.":
        "Χαρμάνια espresso, μονοποικιλιακοί καφέδες, ελληνικός καφές, καφές φίλτρου και σοκολάτα.",
    "Premium beverages and dessert mixes": "Premium ροφήματα και μείγματα γλυκών",
    "Teas, smoothies, milkshakes, granitas, syrups and dessert mixes.":
        "Τσάγια, smoothies, milkshakes, γρανίτες, σιρόπια και μείγματα γλυκών.",
    # Home
    "Vittorio Gourmet Espresso Deliveries all over Cyprus": "Vittorio Gourmet Espresso με παράδοση σε όλη την Κύπρο",
    "Official representative in Cyprus of {vittorio} and {jean_paul}.":
        "Επίσημος αντιπρόσωπος στην Κύπρο της {vittorio} και της {jean_paul}.",
    "Featured products": "Επιλεγμένα προϊόντα",
    "All {group}": "Όλη η κατηγορία",
    "How we work": "Πώς δουλεύουμε",
    "Wholesale & retail": "Χονδρική & λιανική",
    "Delivery across Cyprus": "Παράδοση σε όλη την Κύπρο",
    "Cash on delivery": "Αντικαταβολή",
    "Our brands": "Οι μάρκες μας",
    "Browse {brand}": "Προϊόντα {brand}",
    "Beverages and mixes": "Ροφήματα και μείγματα",
    "For cafés, bars and hotels": "Για καφετέριες, μπαρ και ξενοδοχεία",
    "Espresso machines for partners": "Μηχανές espresso για συνεργάτες",
    "Appia Life, Sanremo and Expobar, at no charge, with free setup and training.":
        "Appia Life, Sanremo και Expobar, χωρίς χρέωση, με δωρεάν εγκατάσταση και εκπαίδευση.",
    # Catalogue page
    "Wholesale & retail range": "Γκάμα χονδρικής & λιανικής",
    "Trade prices plus VAT · Delivery across Cyprus · Cash on delivery":
        "Τιμές χονδρικής πλέον ΦΠΑ · Παράδοση σε όλη την Κύπρο · Αντικαταβολή",
    "Search the catalogue": "Αναζήτηση στον κατάλογο",
    "Search coffees, teas, mixes": "Αναζήτηση: καφές, τσάι, μείγματα",
    "Search": "Αναζήτηση",
    "Brands": "Μάρκες",
    "All brands": "Όλες οι μάρκες",
    "Categories": "Κατηγορίες",
    "All": "Όλα",
    "1 product": "1 προϊόν",
    "{count} products": "{count} προϊόντα",
    "Nothing in the catalogue matches that search.": "Κανένα προϊόν δεν ταιριάζει με την αναζήτηση.",
    # Order and confirmation
    "Delivery order": "Παραγγελία με παράδοση",
    "Cyprus trade delivery · catalogue prices ex VAT · payment on delivery":
        "Παράδοση σε όλη την Κύπρο · τιμές καταλόγου χωρίς ΦΠΑ · πληρωμή κατά την παράδοση",
    "Free Cyprus delivery — this order is over €40 (ex VAT).":
        "Δωρεάν παράδοση — η παραγγελία ξεπερνά τα €40 (χωρίς ΦΠΑ).",
    "Free delivery on orders over €40 (ex VAT).": "Δωρεάν παράδοση για παραγγελίες άνω των €40 (χωρίς ΦΠΑ).",
    "Add {amount} more to qualify.": "Προσθέστε ακόμη {amount} για δωρεάν παράδοση.",
    "Subtotal (ex VAT)": "Υποσύνολο (χωρίς ΦΠΑ)",
    "VAT": "ΦΠΑ",
    "Delivery": "Παράδοση",
    "Free": "Δωρεάν",
    "Total to pay on delivery": "Σύνολο πληρωτέο κατά την παράδοση",
    "Order summary": "Σύνοψη παραγγελίας",
    "Product": "Προϊόν",
    "Pack": "Συσκευασία",
    "Line": "Σύνολο",
    "No photo": "Χωρίς φωτογραφία",
    "Lines without a published price are confirmed before delivery.":
        "Όπου δεν αναγράφεται τιμή, επιβεβαιώνεται πριν από την παράδοση.",
    "Update quantities": "Ενημέρωση ποσοτήτων",
    "Delivery details": "Στοιχεία παράδοσης",
    "Contact name": "Ονοματεπώνυμο",
    "Business name": "Επωνυμία επιχείρησης",
    "(optional)": "(προαιρετικό)",
    "Email": "Email",
    "Phone": "Τηλέφωνο",
    "Delivery town (Cyprus)": "Πόλη παράδοσης (Κύπρος)",
    "Notes for the depot": "Σημειώσεις παραγγελίας",
    "Submitting sends this order to {name} for confirmation. Payment is collected on delivery.":
        "Η παραγγελία αποστέλλεται στη {name} για επιβεβαίωση. Η πληρωμή γίνεται κατά την παράδοση.",
    "Submit order": "Αποστολή παραγγελίας",
    "Your last order": "Η τελευταία σας παραγγελία",
    "Order the same again": "Ίδια παραγγελία ξανά",
    "Your order list is empty.": "Η λίστα παραγγελίας είναι άδεια.",
    "Browse the catalogue": "Δείτε τον κατάλογο",
    "Order confirmation": "Επιβεβαίωση παραγγελίας",
    "Thank you, {name}": "Ευχαριστούμε, {name}",
    "Reference": "Κωδικός",
    "Your order has been sent to Vittorio.": "Η παραγγελία σας στάλθηκε στη Vittorio.",
    "A copy is on its way to {email}.": "Αντίγραφο στάλθηκε στο {email}.",
    "Your order has not reached Vittorio yet. Tap Contact on Viber below and send the message. It already contains your order.":
        "Η παραγγελία σας δεν έχει φτάσει ακόμη στη Vittorio. Πατήστε «Επικοινωνία στο Viber» παρακάτω και στείλτε το μήνυμα. Περιέχει ήδη την παραγγελία σας.",
    "Town": "Πόλη",
    "Business": "Επιχείρηση",
    "Name": "Όνομα",
    "Items": "Προϊόντα",
    "Notes": "Σημειώσεις",
    "Cash on delivery. We confirm every order before delivery.":
        "Πληρωμή με μετρητά κατά την παράδοση. Επιβεβαιώνουμε κάθε παραγγελία πριν από την παράδοση.",
    "Email order": "Αποστολή με email",
    "Return to catalogue": "Επιστροφή στον κατάλογο",
    # Order and contact form errors
    "Add at least one product before placing the order.": "Προσθέστε τουλάχιστον ένα προϊόν πριν στείλετε την παραγγελία.",
    "Enter your name.": "Συμπληρώστε το όνομά σας.",
    "Enter a valid email address.": "Συμπληρώστε ένα έγκυρο email.",
    "Enter a phone number we can reach you on.": "Συμπληρώστε ένα τηλέφωνο επικοινωνίας.",
    "Enter the town in Cyprus for delivery.": "Συμπληρώστε την πόλη παράδοσης στην Κύπρο.",
    "Write a message of at least 10 characters.": "Γράψτε μήνυμα τουλάχιστον 10 χαρακτήρων.",
    "We could not send your message right now. Use Contact on Viber, or try again later.":
        "Δεν ήταν δυνατή η αποστολή του μηνύματος. Επικοινωνήστε στο Viber ή δοκιμάστε ξανά αργότερα.",
    # B2B story
    "Vittorio B2B Services": "Υπηρεσίες B2B της Vittorio",
    "Everything a café needs, from one supplier.": "Ό,τι χρειάζεται μια καφετέρια, από έναν προμηθευτή.",
    "What a partnership includes": "Τι περιλαμβάνει η συνεργασία",
    "Chapters": "Κεφάλαια",
    "Machines": "Μηχανές",
    "Your espresso machine": "Η μηχανή espresso σας",
    "Appia Life, Sanremo or Expobar, on loan at no charge while we work together.":
        "Appia Life, Sanremo ή Expobar, χωρίς χρέωση για όσο διαρκεί η συνεργασία μας.",
    "Setup": "Εγκατάσταση",
    "Installed and explained": "Εγκατάσταση και εκπαίδευση",
    "Free setup guidance and machine training for your staff.":
        "Δωρεάν καθοδήγηση εγκατάστασης και εκπαίδευση του προσωπικού σας στη μηχανή.",
    "Vittorio coffee": "Καφές Vittorio",
    "Espresso blends, single origins, Greek and filter coffee.":
        "Χαρμάνια espresso, μονοποικιλιακοί καφέδες, ελληνικός καφές και καφές φίλτρου.",
    "Beverages": "Ροφήματα",
    "Beyond coffee": "Πέρα από τον καφέ",
    "Jean Paul Lab smoothies, milkshakes, teas, granitas and dessert mixes.":
        "Smoothies, milkshakes, τσάγια, γρανίτες και μείγματα γλυκών της Jean Paul Lab.",
    "Essentials": "Αναλώσιμα",
    "Cups, lids and straws": "Ποτήρια, καπάκια και καλαμάκια",
    "Serviceware for takeaway and the bar.": "Αναλώσιμα για take away και για το μπαρ.",
    "Delivered across Cyprus": "Παράδοση σε όλη την Κύπρο",
    "From Kalo Xorio to your café. Cash on delivery, free over €40.":
        "Από το Καλό Χωριό στο κατάστημά σας. Αντικαταβολή, δωρεάν άνω των €40.",
    "Service": "Σέρβις",
    "Machine service": "Σέρβις μηχανών",
    "We service the machines we supply.": "Κάνουμε σέρβις στις μηχανές που παρέχουμε.",
    "Free setup & training": "Δωρεάν εγκατάσταση & εκπαίδευση",
    "From Kalo Xorio, across Cyprus": "Από το Καλό Χωριό, σε όλη την Κύπρο",
    "Deliveries from Kalo Xorio to Nicosia, Limassol, Paphos, Larnaca and Ayia Napa":
        "Παραδόσεις από το Καλό Χωριό σε Λευκωσία, Λεμεσό, Πάφο, Λάρνακα και Αγία Νάπα",
    "Nicosia": "Λευκωσία",
    "Limassol": "Λεμεσός",
    "Paphos": "Πάφος",
    "Ayia Napa": "Αγία Νάπα",
    "Become a partner": "Γίνετε συνεργάτης",
    "Tell us about your café.": "Πείτε μας για την επιχείρησή σας.",
    "Send a message": "Στείλτε μήνυμα",
    "Jean Paul Lab Blue Night tea": "Τσάι Blue Night της Jean Paul Lab",
    "Jean Paul Lab aromatic chocolate": "Αρωματική σοκολάτα της Jean Paul Lab",
    "Jean Paul Lab mango smoothie": "Smoothie μάνγκο της Jean Paul Lab",
    "Vittorio cups": "Ποτήρια Vittorio",
    "Black lids": "Μαύρα καπάκια",
    "Straws": "Καλαμάκια",
    "Jean Paul Lab waffle mix": "Μείγμα για βάφλες της Jean Paul Lab",
    "Jean Paul Lab chocolate milkshake": "Milkshake σοκολάτα της Jean Paul Lab",
    # Contact, FAQ, legal
    "Contact.": "Επικοινωνία.",
    "Thank you. Use Contact if you need a reply today.":
        "Ευχαριστούμε. Αν χρειάζεστε απάντηση σήμερα, πατήστε Επικοινωνία.",
    "Message": "Μήνυμα",
    "Send": "Αποστολή",
    "Before you order.": "Πριν παραγγείλετε.",
    "Where do you deliver from?": "Από πού γίνεται η παράδοση;",
    "From Kalo Xorio, Larnaca, to anywhere in Cyprus. We do not ship abroad.":
        "Από το Καλό Χωριό Λάρνακας, σε όλη την Κύπρο. Δεν αποστέλλουμε στο εξωτερικό.",
    "How does an order get confirmed?": "Πώς επιβεβαιώνεται μια παραγγελία;",
    "Order on this site or on Viber. We confirm every order before delivery. Prices exclude VAT; payment is cash on delivery.":
        "Παραγγείλετε από τον ιστότοπο ή στο Viber. Επιβεβαιώνουμε κάθε παραγγελία πριν από την παράδοση. Οι τιμές δεν περιλαμβάνουν ΦΠΑ· η πληρωμή γίνεται με μετρητά κατά την παράδοση.",
    "How do returns work?": "Πώς γίνονται οι επιστροφές;",
    "Unopened, unused goods can be returned within 30 days for a refund. You pay return shipping unless the error was ours. Send the order number by email to pantzosantonis@gmail.com, or open Viber.":
        "Κλειστά, αχρησιμοποίητα προϊόντα επιστρέφονται εντός 30 ημερών με επιστροφή χρημάτων. Τα έξοδα επιστροφής βαρύνουν εσάς, εκτός αν το λάθος ήταν δικό μας. Στείλτε τον αριθμό παραγγελίας στο pantzosantonis@gmail.com ή στο Viber.",
    "Are the prices final?": "Είναι οι τιμές τελικές;",
    "Catalogue prices are the published trade prices, shown plus VAT. A line marked “Price not published” is confirmed before delivery.":
        "Οι τιμές του καταλόγου είναι οι δημοσιευμένες τιμές χονδρικής, πλέον ΦΠΑ. Όπου αναγράφεται «Τιμή κατόπιν ζήτησης», η τιμή επιβεβαιώνεται πριν από την παράδοση.",
    "Who do you supply?": "Σε ποιους απευθύνεστε;",
    "Cafés, bars, hotels and retail customers across Cyprus.":
        "Σε καφετέριες, μπαρ, ξενοδοχεία και πελάτες λιανικής σε όλη την Κύπρο.",
    "Which machines do you place?": "Ποιες μηχανές παρέχετε;",
    "Appia Life, Sanremo and Expobar, at no charge for partners, with free setup and training.":
        "Appia Life, Sanremo και Expobar, χωρίς χρέωση για συνεργάτες, με δωρεάν εγκατάσταση και εκπαίδευση.",
    "Do you mark dietary claims?": "Αναγράφετε διατροφικούς ισχυρισμούς;",
    "Only when the product itself states them. We do not add vegan, gluten-free, or similar marks that the listing does not carry.":
        "Μόνο όταν τους αναφέρει το ίδιο το προϊόν. Δεν προσθέτουμε ενδείξεις όπως vegan ή χωρίς γλουτένη, αν δεν υπάρχουν στην περιγραφή του.",
    "What we keep.": "Τι κρατάμε.",
    "An order list stays in your browser until you place it. Submitting the order emails it to the depot and sends you a copy. Payment is cash on delivery only; we do not take card details on this site.":
        "Η λίστα παραγγελίας μένει στον browser σας μέχρι να τη στείλετε. Με την αποστολή, η παραγγελία πηγαίνει με email στην αποθήκη και λαμβάνετε αντίγραφο. Η πληρωμή γίνεται μόνο με μετρητά κατά την παράδοση· δεν ζητάμε στοιχεία κάρτας σε αυτόν τον ιστότοπο.",
    "After an order, this browser remembers your delivery details and last order for a year. Clearing cookies removes them.":
        "Μετά από μια παραγγελία, ο browser θυμάται τα στοιχεία παράδοσης και την τελευταία σας παραγγελία για ένα χρόνο. Διαγράφονται μαζί με τα cookies.",
    "The contact form asks for a name, an email, and a message. Submitting it sends that note to the depot inbox. Use Contact when you need a reply the same day.":
        "Η φόρμα επικοινωνίας ζητά όνομα, email και μήνυμα, τα οποία στέλνονται στο email της αποθήκης. Για απάντηση την ίδια μέρα, πατήστε Επικοινωνία.",
    "Questions about an order go to {email} or {contact}.":
        "Για ερωτήσεις σχετικά με μια παραγγελία, γράψτε στο {email} ή πατήστε {contact}.",
    "If something should come back.": "Επιστροφές προϊόντων.",
    "Unopened, unused products can be returned within 30 days of purchase for a refund.":
        "Κλειστά, αχρησιμοποίητα προϊόντα επιστρέφονται εντός 30 ημερών από την αγορά, με επιστροφή χρημάτων.",
    "Start the return with the order number by email at pantzosantonis@gmail.com, or {contact}.":
        "Ξεκινήστε την επιστροφή στέλνοντας τον αριθμό παραγγελίας στο pantzosantonis@gmail.com ή πατήστε {contact}.",
    "Return shipping is yours to cover, unless the fault was ours.":
        "Τα έξοδα επιστροφής βαρύνουν εσάς, εκτός αν το λάθος ήταν δικό μας.",
    "Damaged or wrong goods should be reported as soon as they arrive, for a replacement or a refund.":
        "Κατεστραμμένα ή λάθος προϊόντα δηλώνονται μόλις παραληφθούν, για αντικατάσταση ή επιστροφή χρημάτων.",
    "Orders are placed on this site and emailed to the depot. Payment is cash on delivery. A refund, once agreed, is arranged the same way.":
        "Οι παραγγελίες γίνονται σε αυτόν τον ιστότοπο και στέλνονται με email στην αποθήκη. Η πληρωμή γίνεται με μετρητά κατά την παράδοση. Η επιστροφή χρημάτων, όταν συμφωνηθεί, γίνεται με τον ίδιο τρόπο.",
    "A standing order can be stopped by writing to the same team. Any refund covers shipments that have not yet left.":
        "Μια πάγια παραγγελία διακόπτεται με γραπτό αίτημα στην ίδια ομάδα. Η επιστροφή χρημάτων αφορά αποστολές που δεν έχουν ακόμη αναχωρήσει.",
    "This page is not in the house.": "Η σελίδα δεν βρέθηκε.",
    "View the catalogue": "Δείτε τον κατάλογο",
    # Pages outside the nav
    "Visit": "Επίσκεψη",
    "The depot in Kalo Xorio.": "Η αποθήκη στο Καλό Χωριό.",
    "We deliver across Cyprus from Kalo Xorio.": "Παραδίδουμε σε όλη την Κύπρο από το Καλό Χωριό.",
    "Larnaca district": "Επαρχία Λάρνακας",
    "Orders": "Παραγγελίες",
    "Directions": "Οδηγίες πρόσβασης",
    "Supply": "Προμήθεια",
    "Cyprus-wide delivery.": "Παράδοση σε όλη την Κύπρο.",
    "Wholesale and retail · delivery across Cyprus": "Χονδρική και λιανική · παράδοση σε όλη την Κύπρο",
    "Coffee, chocolate, teas, syrups, mixes, serviceware": "Καφές, σοκολάτα, τσάγια, σιρόπια, μείγματα, αναλώσιμα",
    "Cafés, bars, and retail customers": "Καφετέριες, μπαρ και πελάτες λιανικής",
    "Prices plus VAT": "Τιμές πλέον ΦΠΑ",
    "Story": "Ιστορία",
    "Built for the counter.": "Φτιαγμένο για τον πάγκο.",
    "Vittorio grew up around quality and service, first in Greece, then as a supplier for people who serve coffee every day. In Cyprus the work is based in Kalo Xorio, Larnaca.":
        "Η Vittorio μεγάλωσε με γνώμονα την ποιότητα και την εξυπηρέτηση, πρώτα στην Ελλάδα και έπειτα ως προμηθευτής για όσους σερβίρουν καφέ κάθε μέρα. Στην Κύπρο, η βάση μας είναι το Καλό Χωριό Λάρνακας.",
    "The brief is simple: good goods, people who know the range, and support after the delivery, for professionals and for home drinkers.":
        "Ο στόχος είναι απλός: καλά προϊόντα, άνθρωποι που γνωρίζουν την γκάμα και υποστήριξη μετά την παράδοση, για επαγγελματίες και για το σπίτι.",
    "In February 2019 the team exhibited at HO.RE.CA. in Athens, then thanked everyone who came to the 14th edition. Those notes are in the journal.":
        "Τον Φεβρουάριο του 2019 η ομάδα συμμετείχε στην HO.RE.CA. στην Αθήνα και ευχαρίστησε όσους επισκέφθηκαν τη 14η διοργάνωση. Οι σημειώσεις βρίσκονται στο ημερολόγιο.",
    "Read the notes": "Διαβάστε τις σημειώσεις",
    "Philosophy": "Φιλοσοφία",
    "The cup is the work.": "Το φλιτζάνι είναι το έργο μας.",
    "Specialty coffee is a meeting point: the people who grow it, the people who roast it, and the barista who serves it. Vittorio exists so that meeting can happen every day behind a Cypriot bar.":
        "Ο specialty καφές είναι σημείο συνάντησης: όσων τον καλλιεργούν, όσων τον καβουρδίζουν και του barista που τον σερβίρει. Η Vittorio υπάρχει ώστε αυτή η συνάντηση να γίνεται κάθε μέρα πίσω από έναν κυπριακό πάγκο.",
    "We supply carefully chosen goods, stay with the sale, and stay after it. The same standard holds for a professional counter and for someone making coffee at home.":
        "Προμηθεύουμε προσεκτικά επιλεγμένα προϊόντα και είμαστε δίπλα στον πελάτη πριν και μετά την πώληση. Το ίδιο πρότυπο ισχύει για τον επαγγελματικό πάγκο και για όποιον φτιάχνει καφέ στο σπίτι.",
    "The catalogue is the proof. What we list is what we deliver.":
        "Ο κατάλογος είναι η απόδειξη. Ό,τι αναφέρουμε, αυτό παραδίδουμε.",
    "Coffees in the catalogue": "Οι καφέδες του καταλόγου",
    "Equipment": "Εξοπλισμός",
    "Espresso machine programmes.": "Προγράμματα μηχανών espresso.",
    "No charge for the machine while the partnership continues · free setup guidance":
        "Χωρίς χρέωση για τη μηχανή όσο διαρκεί η συνεργασία · δωρεάν καθοδήγηση εγκατάστασης",
    "Appia Life three-group commercial espresso machine in black and stainless steel.":
        "Επαγγελματική μηχανή espresso Appia Life τριών γκρουπ, σε μαύρο και ανοξείδωτο ατσάλι.",
    "Sanremo Café Racer three-group espresso machine in black and stainless steel.":
        "Μηχανή espresso Sanremo Café Racer τριών γκρουπ, σε μαύρο και ανοξείδωτο ατσάλι.",
    "Expobar two-group commercial espresso machine in polished stainless steel with black accents.":
        "Επαγγελματική μηχανή espresso Expobar δύο γκρουπ, από γυαλισμένο ανοξείδωτο ατσάλι με μαύρες λεπτομέρειες.",
    "Journal": "Ημερολόγιο",
    "From the trade floor.": "Από τις εκθέσεις.",
    "Two notes from HO.RE.CA. 2019, when Vittorio met the hospitality trade in Athens.":
        "Δύο σημειώσεις από την HO.RE.CA. 2019, όταν η Vittorio συνάντησε τον κλάδο της φιλοξενίας στην Αθήνα.",
    "All notes": "Όλες οι σημειώσεις",
    "A stand at HO.RE.CA. 2019": "Περίπτερο στην HO.RE.CA. 2019",
    "8–11 February 2019": "8–11 Φεβρουαρίου 2019",
    "Vittorio met the trade at HO.RE.CA. 2019, Metropolitan Expo, Athens.":
        "Η Vittorio συνάντησε τον κλάδο στην HO.RE.CA. 2019, στο Metropolitan Expo της Αθήνας.",
    "In February 2019 Vittorio took a stand at HO.RE.CA., the hospitality exhibition in Athens.":
        "Τον Φεβρουάριο του 2019 η Vittorio συμμετείχε με περίπτερο στην HO.RE.CA., την έκθεση φιλοξενίας της Αθήνας.",
    "The invitation named Metropolitan Expo, Hall 1, stand C12/D11, and the dates 8–11 February.":
        "Η πρόσκληση ανέφερε Metropolitan Expo, Αίθουσα 1, περίπτερο C12/D11, 8–11 Φεβρουαρίου.",
    "The team was there to talk through the range with people who run bars, cafés, and hotels.":
        "Η ομάδα ήταν εκεί για να παρουσιάσει την γκάμα σε όσους διαχειρίζονται μπαρ, καφετέριες και ξενοδοχεία.",
    "After the 14th HORECA": "Μετά τη 14η HORECA",
    "February 2019": "Φεβρουάριος 2019",
    "A note of thanks after the 14th HORECA, written first in Greek.": "Ευχαριστήριο σημείωμα μετά τη 14η HORECA.",
    "When the 14th HORECA closed, Vittorio posted a thank-you. The original note is in Greek.":
        "Με το κλείσιμο της 14ης HORECA, η Vittorio δημοσίευσε ένα ευχαριστήριο σημείωμα.",
    "It thanks everyone who came to the stand, and looks ahead to meeting them again the following year.":
        "Ευχαριστεί όλους όσοι επισκέφθηκαν το περίπτερο και ανυπομονεί να τους συναντήσει ξανά την επόμενη χρονιά.",
    # Page titles and meta descriptions
    "Vittorio Gourmet Espresso — wholesale & retail coffee in Cyprus":
        "Vittorio Gourmet Espresso — καφές χονδρικής & λιανικής στην Κύπρο",
    "Official Cyprus representative of Vittorio Gourmet Espresso and Jean Paul Lab. Coffee, beverages and café mixes with published trade prices, delivered across Cyprus.":
        "Επίσημος αντιπρόσωπος στην Κύπρο της Vittorio Gourmet Espresso και της Jean Paul Lab. Καφές, ροφήματα και μείγματα με δημοσιευμένες τιμές χονδρικής και παράδοση σε όλη την Κύπρο.",
    "Catalogue — Vittorio Gourmet Espresso": "Κατάλογος — Vittorio Gourmet Espresso",
    "Vittorio coffee and Jean Paul Lab beverages, teas, mixes and café supplies, with published trade prices plus VAT and delivery across Cyprus.":
        "Καφές Vittorio και ροφήματα, τσάγια και μείγματα Jean Paul Lab, με δημοσιευμένες τιμές χονδρικής πλέον ΦΠΑ και παράδοση σε όλη την Κύπρο.",
    "Coffee philosophy — Vittorio Gourmet Espresso": "Φιλοσοφία — Vittorio Gourmet Espresso",
    "How Vittorio thinks about coffee for the bar, and the coffees in the Cyprus catalogue.":
        "Πώς βλέπει η Vittorio τον καφέ για το μπαρ, και οι καφέδες του καταλόγου στην Κύπρο.",
    "Our story — Vittorio Gourmet Espresso": "Η ιστορία μας — Vittorio Gourmet Espresso",
    "Vittorio supplies the Cypriot bar from a depot in Kalo Xorio, and met the trade at HO.RE.CA. 2019.":
        "Η Vittorio εφοδιάζει τα κυπριακά μπαρ από την αποθήκη στο Καλό Χωριό και συνάντησε τον κλάδο στην HO.RE.CA. 2019.",
    "Coffee supply — Vittorio Gourmet Espresso": "Προμήθεια καφέ — Vittorio Gourmet Espresso",
    "Coffee and café supplies delivered to cafés and bars across Cyprus.":
        "Καφές και αναλώσιμα για καφετέριες και μπαρ σε όλη την Κύπρο.",
    "B2B Services — Vittorio Gourmet Espresso Cyprus": "Υπηρεσίες B2B — Vittorio Gourmet Espresso Κύπρου",
    "Wholesale coffee, machines, training, and partner supply for cafés and bars across Cyprus.":
        "Καφές χονδρικής, μηχανές, εκπαίδευση και εφοδιασμός για καφετέριες και μπαρ σε όλη την Κύπρο.",
    "Coffee machines — Vittorio Gourmet Espresso": "Μηχανές καφέ — Vittorio Gourmet Espresso",
    "Appia Life, Sanremo, and Expobar machines are offered with no charge during a partnership. Setup guidance is free once cooperation starts.":
        "Μηχανές Appia Life, Sanremo και Expobar χωρίς χρέωση κατά τη διάρκεια της συνεργασίας, με δωρεάν καθοδήγηση εγκατάστασης.",
    "Your order — Vittorio Gourmet Espresso": "Η παραγγελία σας — Vittorio Gourmet Espresso",
    "Place a coffee and café-supply order for delivery in Cyprus.":
        "Παραγγείλετε καφέ και αναλώσιμα με παράδοση στην Κύπρο.",
    "Order received — Vittorio Gourmet Espresso": "Η παραγγελία ελήφθη — Vittorio Gourmet Espresso",
    "Your Cyprus delivery order is emailed to the depot. Payment is cash on delivery only.":
        "Η παραγγελία σας στάλθηκε. Η πληρωμή γίνεται μόνο με μετρητά κατά την παράδοση.",
    "Visit us — Vittorio Gourmet Espresso, Kalo Xorio": "Επισκεφθείτε μας — Vittorio Gourmet Espresso, Καλό Χωριό",
    "The Vittorio depot in Kalo Xorio, Larnaca, Cyprus.": "Η αποθήκη της Vittorio στο Καλό Χωριό Λάρνακας, Κύπρος.",
    "Journal — Vittorio Gourmet Espresso": "Ημερολόγιο — Vittorio Gourmet Espresso",
    "Notes from Vittorio at HO.RE.CA. 2019 in Athens.": "Σημειώσεις της Vittorio από την HO.RE.CA. 2019 στην Αθήνα.",
    "Contact — Vittorio Gourmet Espresso": "Επικοινωνία — Vittorio Gourmet Espresso",
    "Reach the Vittorio depot in Kalo Xorio on Viber.": "Επικοινωνήστε με τη Vittorio στο Καλό Χωριό μέσω Viber.",
    "Questions — Vittorio Gourmet Espresso": "Ερωτήσεις — Vittorio Gourmet Espresso",
    "Delivery, machines, returns, and how an order is confirmed.":
        "Παράδοση, μηχανές, επιστροφές και επιβεβαίωση παραγγελιών.",
    "Privacy — Vittorio Gourmet Espresso": "Απόρρητο — Vittorio Gourmet Espresso",
    "What Vittorio keeps from an order or a message on this site.":
        "Ποια στοιχεία κρατά η Vittorio από μια παραγγελία ή ένα μήνυμα σε αυτόν τον ιστότοπο.",
    "Returns — Vittorio Gourmet Espresso": "Επιστροφές — Vittorio Gourmet Espresso",
    "Unopened goods can be returned within 30 days. Orders are cash on delivery.":
        "Κλειστά προϊόντα επιστρέφονται εντός 30 ημερών. Πληρωμή με αντικαταβολή.",
    "Page not found — Vittorio Gourmet Espresso": "Η σελίδα δεν βρέθηκε — Vittorio Gourmet Espresso",
    "That page is not part of Vittorio Gourmet Espresso.": "Αυτή η σελίδα δεν υπάρχει στον ιστότοπο της Vittorio Gourmet Espresso.",
    # Customer copy email
    "Dear {name},": "Γεια σας {name},",
    "Thank you for your order with {business}. We will confirm it before delivery.":
        "Σας ευχαριστούμε για την παραγγελία σας στη {business}. Θα την επιβεβαιώσουμε πριν από την παράδοση.",
    "Order reference: {ref}": "Κωδικός παραγγελίας: {ref}",
    "Delivery to: {town}, Cyprus": "Παράδοση: {town}, Κύπρος",
    "Business: {name}": "Επιχείρηση: {name}",
    "Payment: cash on delivery only.": "Πληρωμή: μόνο με μετρητά κατά την παράδοση.",
    "Order the same again:": "Ίδια παραγγελία ξανά:",
    "Questions about your order? Reply to this email.": "Ερωτήσεις για την παραγγελία σας; Απαντήστε σε αυτό το email.",
    "Your Vittorio order {ref}": "Η παραγγελία σας Vittorio {ref}",
}

STRINGS = {"el": EL}


def translate(text, lang, **values):
    """Greek for an English string (English when no translation exists), then fill {placeholders}."""
    if lang != DEFAULT_LANG:
        text = STRINGS.get(lang, {}).get(text, text)
    return text.format(**values) if values else text


def lang_for_path(path):
    return "el" if path == "/el" or path.startswith("/el/") else DEFAULT_LANG


def localize_pack(label, lang):
    if lang == "el" and label:
        return re.sub(r"\bpcs\b", "τεμ.", label)
    return label


def fold(text):
    """Case- and accent-insensitive form for search, so 'σοκολατα' finds 'σοκολάτα'."""
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


# Greek product copy, keyed by slug: description, and profile/dietary where English has them.
PRODUCTS_EL = json.loads((ROOT / "data" / "products_el.json").read_text(encoding="utf-8"))


def _greek_price_label(label):
    if label in EL:
        return EL[label]
    return label.replace("+ VAT", "+ ΦΠΑ")


def _greek_product(item):
    greek = dict(item)
    greek.update(PRODUCTS_EL.get(item["slug"], {}))
    greek["price_label"] = _greek_price_label(item["price_label"])
    return greek


def _greek_catalog():
    products = [_greek_product(item) for item in PRODUCTS]
    by_slug = {item["slug"]: item for item in products}
    brands = [dict(brand, products=[by_slug[slug] for slug in brand["showcase"]]) for brand in BRANDS]
    packs = []
    for pack in HERO["packs"]:
        product = by_slug[pack["slug"]]
        packs.append(
            dict(
                pack,
                description=product.get("description", ""),
                price_label=product["price_label"],
                size=localize_pack(pack["size"], "el"),
            )
        )
    return {"products": products, "by_slug": by_slug, "brands": brands, "hero": dict(HERO, packs=packs)}


CATALOGS = {
    "en": {"products": PRODUCTS, "by_slug": PRODUCTS_BY_SLUG, "brands": BRANDS, "hero": HERO},
    "el": _greek_catalog(),
}

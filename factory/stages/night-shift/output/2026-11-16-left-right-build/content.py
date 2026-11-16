"""Left Right Christmas Game: 6 original stories. Every LEFT/RIGHT (caps) is a pass cue; STEAL is story 5's twist cue.
Paragraphs split by blank lines. {1}..{6} in TYPEIN are type-in name fields."""

STORIES = [
 dict(key="family", title="The Family Christmas Countdown", crowd="Family", ages="All ages", text="""
It was Christmas Eve, and the whole family was rushing LEFT and RIGHT. Mom read the list and gasped. "Who LEFT the pie in the car?" Dad raised his RIGHT hand and LEFT the room very quickly.

Grandma stirred the gravy with her LEFT hand and swatted cookie thieves with her RIGHT. Grandpa turned the oven dial LEFT, then RIGHT, and said the turkey needed ten more minutes. He was RIGHT, except he had been saying it for two hours.

The twins hung the lights. One started on the LEFT side of the house, the other on the RIGHT, and they met at the front door with one plug and no outlet. Dad said it looked RIGHT from the street if you squinted.

Uncle Joe arrived with a gift wrapped in newspaper and three rolls of tape. "I'm not sure I wrapped it RIGHT," he said. The cousins shook it anyway and LEFT it under the tree, where the cat sat on it RIGHT away.

At dinner, the potatoes went RIGHT and the gravy went LEFT, so the bowls met in the middle and nobody got anything. Grandma said we would try again, RIGHT after grace, and pass everything LEFT.

Then the doorbell rang. The neighbors had LEFT a plate of fudge on the step, so Mom ran RIGHT out to say thank you, and the dog ran LEFT past her to say hello. The cat ran RIGHT up the tree. Grandpa said he had seen this coming, which was RIGHT, because he had LEFT the door open.

After pie, one last gift turned up, LEFT in the hall closet since July. Nobody knew who it was for. So whoever holds a gift when this story ends keeps it. Hold on tight, because this story is over RIGHT ... about ... NOW. Merry Christmas!
"""),
 dict(key="office", title="The Office Party Memo", crowd="Office and adults", ages="Teens and up", text="""
Attention all staff: the holiday party starts RIGHT after lunch, or RIGHT after the two o'clock meeting, depending on who LEFT the calendar invite half finished.

To find it, turn LEFT at the copy machine and RIGHT at the plant nobody waters. The team on the LEFT side of the office decorated, using every roll of tape LEFT in the supply closet. The team on the RIGHT side has questions.

The potluck sheet is RIGHT by the coffee maker. So far: eleven bags of chips and a casserole someone LEFT in the fridge last Thursday. If it is yours, claim it RIGHT away. If not, do not open it. Do not even look at it.

The printer is still broken. Tech support says it is not the RIGHT kind of broken, so it has been LEFT for the building manager, who LEFT for vacation.

Music: the speaker on the LEFT plays carols, the speaker on the RIGHT plays the hold music from the phone system, and nobody knows how to turn either one off. Please sing along with the one on your LEFT, and smile politely at the one on your RIGHT.

Last, the gift swap: one gift under twenty dollars that is not a mug. Last year the only person who LEFT without a mug got a smaller mug. Bring the RIGHT gift and nobody gets hurt.

One more thing about parking: please park on the LEFT side of the lot, because the RIGHT side is where the snow plow piles everything. Whoever LEFT a car there last year can still see the antenna. If you get lost, turn RIGHT at the giant inflatable penguin, then LEFT at the second giant inflatable penguin.

Thank you for reading RIGHT to the end. Happy holidays from the party committee, which is just Pat, who LEFT early.
"""),
 dict(key="kids", title="The Snowman's Missing Mitten", crowd="Kids and classrooms", ages="Ages 4 and up", text="""
One snowy morning, two kids built a snowman RIGHT in the middle of the yard. He had a carrot nose, two stick arms and one red mitten on his LEFT hand. But the mitten for his RIGHT hand was missing!

"We LEFT it inside!" said the little sister. They ran RIGHT in, LEFT their boots by the door and looked everywhere. Not under the couch on the LEFT. Not behind the tree on the RIGHT. Not even in the cookie jar, which they checked twice, just to be sure.

Meanwhile, the puppy had found the mitten RIGHT where it fell. He trotted out, turned LEFT at the mailbox, turned RIGHT at the bird feeder and buried it in the snow like treasure.

A squirrel watched from the fence on the LEFT. A bird watched from the branch on the RIGHT. Nobody told the kids a thing.

When the kids came back, the snowman's RIGHT arm was gone too! The puppy sat RIGHT beside him, wagging, with the stick in his mouth. "Drop it!" said the big brother. The puppy ran LEFT. "Come back!" said the little sister. The puppy ran RIGHT, then LEFT again, just for fun.

The kids made a plan. The big brother would sneak up on the LEFT. The little sister would sneak up on the RIGHT. The puppy, who was very smart, sat RIGHT in the middle and waited. When they jumped, he LEFT, and the two kids landed in the snow, nose to nose, RIGHT where the puppy used to be.

At last the puppy flopped down in the snow, RIGHT on top of the missing mitten. The kids laughed, dug it out and gave the puppy a biscuit LEFT over from breakfast. "Now our snowman looks just RIGHT," said the big brother, and nobody was LEFT out in the cold. The End!
"""),
 dict(key="nativity", title="The Road to Bethlehem", crowd="Church, family and Sunday school", ages="All ages", text="""
Long ago, Mary and Joseph LEFT their home in Nazareth. Everyone had to be counted in their family's town, so they set out RIGHT away.

The road was long and dusty. Mary rode a little donkey, and Joseph walked RIGHT beside her, past hills on the LEFT and fields on the RIGHT. Each night they rested, and each morning they LEFT again at sunrise, with the sun RIGHT in their eyes.

In Bethlehem, the town was full. Joseph knocked on a door on the LEFT, then a door on the RIGHT, then one more on the LEFT and one more on the RIGHT, and every innkeeper shook his head. At last a kind man pointed to a stable RIGHT behind his house. It was not fancy, but it was warm, and it was the RIGHT place.

That night baby Jesus was born. Mary wrapped him snugly and laid him in a manger, RIGHT there among the sheep, the cows and the little donkey.

On a hillside, shepherds were watching their flocks when an angel appeared and told them that a Savior had been born that night in Bethlehem. They LEFT their sheep and hurried into town, turning LEFT and RIGHT through the narrow streets until they found the baby, just as the angel had said.

Far to the east, wise men saw a new star. They followed it LEFT and RIGHT across the desert for many days, and when they found the child, they knelt and LEFT their gifts: gold, frankincense and myrrh.

The shepherds told everyone they met what they had seen. People on the LEFT side of the street stopped to listen, and people on the RIGHT side came over too. Mary kept all these things RIGHT in her heart, and the shepherds LEFT praising God, singing all the way back to their sheep.

The best gift of all was never LEFT under a tree. It came that first Christmas night, and it is still RIGHT here for everyone. Merry Christmas!
"""),
 dict(key="steal", title="The Gift Nobody Wanted", crowd="White elephant and gift swaps", ages="Teens and up", steal=True, text="""
Every white elephant swap has one gift nobody wants. This year it was a lumpy gold box, sitting RIGHT on top of the pile.

Uncle Ray went first. He shook it, heard a slosh on the LEFT side and a rattle on the RIGHT, and decided to STEAL the candle instead.

Grandma tore the gold box open RIGHT away. Inside: one sock, a very old fruitcake and a note that said, "Nice try. Pass me to the LEFT."

The cousin on her LEFT tried to trade it for a gift card. The cousin on her RIGHT pretended to be asleep. Dad, RIGHT across the room, said someone should STEAL it while they still could.

Nobody did. The box went LEFT, then RIGHT, then LEFT again, until the dog grabbed the sock and ran RIGHT out the door. Aunt Sue chased him LEFT around the couch and RIGHT around the tree, and came back with the sock and half a bow.

By now the candle had changed hands three times, and the gift card was LEFT under the couch where nobody could reach it. Someone said the RIGHT thing to do was start over. Everybody said no.

Grandpa tried to STEAL his own gift back. That is not allowed, said the cousin on his RIGHT. That is not even possible, said the cousin on his LEFT. Grandpa said the rules were not written down RIGHT, so he LEFT the room to find a pen, and came back with a list of rules that all started with Grandpa wins. Grandma read it, turned it over, folded it LEFT, then RIGHT, then LEFT again, and made it into a paper hat. It fit him RIGHT away.

Mom was the only one LEFT without a gift. "I will STEAL ... the fruitcake," she said. Everyone gasped. She added ice cream, and it was gone in five minutes. It turns out the RIGHT gift is the one you laugh about all year. Merry Christmas!
"""),
 dict(key="short", title="The Last-Minute Shopper", crowd="Quick game, any group", ages="All ages", short=True, text="""
Ted waited until Christmas Eve to shop. He ran RIGHT to the mall, turned LEFT at the food court, turned RIGHT at the toy store and looked LEFT, looked RIGHT, and found one thing LEFT on the shelf: a singing toy fish.

"Is this the RIGHT gift for my wife?" Ted asked. "Sir," said the clerk, "it is the only gift LEFT."

Ted paid, ran out the door, turned RIGHT, turned LEFT, and realized he had LEFT his car keys RIGHT on the counter.

On the drive home, the fish started singing. Ted turned the radio knob LEFT, then RIGHT, but the fish only sang louder.

At the next red light, Ted looked LEFT, then RIGHT, and saw two more last-minute shoppers, each holding a singing fish.

He made it home RIGHT before midnight and walked RIGHT in. His wife opened the box, pushed the button and laughed until she cried. "It's perfect," she said. "Now pass it to the LEFT!" Merry Christmas!
"""),
]

TYPEIN = """
It was Christmas Eve, and the whole family was rushing LEFT and RIGHT. {1} read the list and gasped. "Who LEFT the pie in the car?" {2} raised a RIGHT hand and LEFT the room very quickly.

{3} stirred the gravy and guarded the cookies with a spoon held RIGHT up high. {4} turned the oven dial LEFT, then RIGHT, and said the turkey needed ten more minutes, which had been true for two hours.

{5} arrived with a gift wrapped in newspaper. "I'm not sure I wrapped it RIGHT." Everyone shook it anyway and LEFT it under the tree.

At dinner, the potatoes went RIGHT and the gravy went LEFT, so nobody got anything. {6} solved it by eating the stuffing RIGHT out of the pan.

Whoever holds a gift when this story ends keeps it. Hold on tight, because this story is over RIGHT ... about ... NOW. Merry Christmas!
"""
TYPEIN_ROLES = ["The list maker", "The one who forgets things", "The best cook", "The turkey timer", "The worst gift wrapper", "The hungriest guest"]
